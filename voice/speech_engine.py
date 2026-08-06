"""
Reliable local speech-to-text engine for Voice Incident Reporting.

Key improvements:
- base.en model support for better short-code accuracy
- mild audio cleaning instead of aggressive speech distortion
- dual-pass transcription (original + cleaned audio)
- field-aware decoding for identifiers, digits, dates and narratives
- automatic best-candidate selection
"""

from __future__ import annotations

import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import noisereduce as nr
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel


class SpeechRecognitionEngine:
    """Transcribe Streamlit microphone recordings with faster-whisper."""

    SHORT_FIELD_TYPES = {
        "identifier",
        "digits",
        "latitude",
        "longitude",
        "date",
        "yes_no",
        "federal_state",
    }

    def __init__(
        self,
        model_size: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

    @staticmethod
    def _prepare_audio(source_path: str, output_path: str) -> Dict[str, Any]:
        """Create a gently cleaned mono WAV without damaging short speech."""
        audio, sample_rate = sf.read(
            source_path,
            always_2d=False,
            dtype="float32",
        )

        if audio is None or np.size(audio) == 0:
            raise ValueError("The audio recording is empty.")

        audio_array = np.asarray(audio, dtype=np.float32)
        if audio_array.ndim == 2:
            audio_array = np.mean(audio_array, axis=1, dtype=np.float32)

        audio_array = np.nan_to_num(
            audio_array,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )
        audio_array = audio_array - float(np.mean(audio_array))

        duration_seconds = len(audio_array) / float(sample_rate)
        if duration_seconds < 0.25:
            raise ValueError(
                "The recording is too short. Please speak for at least half a second."
            )

        peak_before = float(np.max(np.abs(audio_array)))
        rms = float(np.sqrt(np.mean(np.square(audio_array))))
        if peak_before < 1e-5 or rms < 1e-6:
            raise ValueError(
                "No usable speech was detected. Please move closer to the microphone."
            )

        noise_reduction_applied = False
        try:
            reduced = nr.reduce_noise(
                y=audio_array,
                sr=sample_rate,
                stationary=False,
                prop_decrease=0.35,
            )
            if reduced is not None and len(reduced) == len(audio_array):
                reduced = np.asarray(reduced, dtype=np.float32)
                # Keep the original when reduction removes too much energy.
                reduced_rms = float(np.sqrt(np.mean(np.square(reduced))))
                if reduced_rms >= rms * 0.45:
                    audio_array = reduced
                    noise_reduction_applied = True
        except Exception:
            noise_reduction_applied = False

        peak = float(np.max(np.abs(audio_array)))
        if peak > 0:
            audio_array = np.clip(audio_array * (0.88 / peak), -1.0, 1.0)

        sf.write(
            output_path,
            audio_array.astype(np.float32),
            sample_rate,
            subtype="PCM_16",
        )

        return {
            "sample_rate": int(sample_rate),
            "duration_seconds": float(duration_seconds),
            "noise_reduction_applied": noise_reduction_applied,
            "input_peak": peak_before,
            "input_rms": rms,
        }

    def _transcribe_path(
        self,
        path: str,
        *,
        language: str,
        prompt: str | None,
        field_type: str,
        use_vad: bool,
    ) -> Tuple[str, Any, float]:
        """Run one transcription pass and return text, metadata and score."""
        short_field = field_type in self.SHORT_FIELD_TYPES

        segments, information = self.model.transcribe(
            path,
            language=language,
            beam_size=8 if short_field else 5,
            best_of=8 if short_field else 5,
            temperature=0.0,
            vad_filter=use_vad,
            vad_parameters=(
                {
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400,
                }
                if use_vad
                else None
            ),
            condition_on_previous_text=False,
            word_timestamps=False,
            initial_prompt=prompt or None,
            no_speech_threshold=0.7,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
        )

        parts: List[str] = []
        log_probs: List[float] = []
        no_speech_probs: List[float] = []

        for segment in segments:
            text = str(segment.text).strip()
            if text:
                parts.append(text)
                log_probs.append(float(getattr(segment, "avg_logprob", -2.0)))
                no_speech_probs.append(float(getattr(segment, "no_speech_prob", 1.0)))

        transcript = " ".join(parts).strip()
        avg_logprob = sum(log_probs) / len(log_probs) if log_probs else -10.0
        avg_no_speech = (
            sum(no_speech_probs) / len(no_speech_probs)
            if no_speech_probs
            else 1.0
        )
        score = avg_logprob - avg_no_speech
        return transcript, information, score

    @staticmethod
    def _candidate_bonus(text: str, field_type: str) -> float:
        """Prefer candidates shaped correctly for the current field."""
        if not text:
            return -100.0

        value = text.strip()
        lower = value.lower().strip(" .,!?")
        bonus = 0.0

        if field_type == "digits":
            digit_count = len(re.findall(r"\d", value))
            number_words = len(
                re.findall(
                    r"\b(?:zero|oh|one|two|three|four|five|six|seven|eight|nine|double|triple)\b",
                    lower,
                )
            )
            bonus += min(digit_count + number_words, 12) * 0.12
            bonus -= len(re.findall(r"[a-z]+", lower)) * 0.03

        elif field_type == "identifier":
            useful = len(re.findall(r"[a-zA-Z0-9]", value))
            bonus += min(useful, 16) * 0.06

        elif field_type in {"latitude", "longitude"}:
            if re.search(r"\d", value):
                bonus += 0.5
            if "." in value or "point" in lower or "dot" in lower:
                bonus += 0.35

        elif field_type == "yes_no":
            if re.search(r"\b(?:yes|yeah|yep|no|nope)\b", lower):
                bonus += 1.0

        elif field_type == "federal_state":
            if "federal" in lower or re.search(r"\bstate\b", lower):
                bonus += 1.0

        elif field_type == "narrative":
            bonus += min(len(value.split()), 30) * 0.025

        return bonus

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "en",
        prompt: str | None = None,
        field_type: str = "text",
    ) -> Dict[str, Any]:
        """Transcribe a Streamlit WAV recording using field-aware dual passes."""
        if not audio_bytes:
            raise ValueError("The audio recording is empty.")

        start_time = time.perf_counter()
        source_path: str | None = None
        cleaned_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as source_file:
                source_file.write(audio_bytes)
                source_path = source_file.name

            with tempfile.NamedTemporaryFile(
                suffix="_clean.wav", delete=False
            ) as cleaned_file:
                cleaned_path = cleaned_file.name

            audio_metadata = self._prepare_audio(source_path, cleaned_path)
            short_field = field_type in self.SHORT_FIELD_TYPES

            candidates: List[Dict[str, Any]] = []

            # Original audio is usually safest for short IDs and numbers.
            original_text, original_info, original_score = self._transcribe_path(
                source_path,
                language=language,
                prompt=prompt,
                field_type=field_type,
                use_vad=False if short_field else True,
            )
            if original_text:
                candidates.append(
                    {
                        "source": "original",
                        "text": original_text,
                        "information": original_info,
                        "score": original_score
                        + self._candidate_bonus(original_text, field_type),
                    }
                )

            # Cleaned pass can help with fan noise and longer narratives.
            cleaned_text, cleaned_info, cleaned_score = self._transcribe_path(
                cleaned_path,
                language=language,
                prompt=prompt,
                field_type=field_type,
                use_vad=False if short_field else True,
            )
            if cleaned_text:
                candidates.append(
                    {
                        "source": "cleaned",
                        "text": cleaned_text,
                        "information": cleaned_info,
                        "score": cleaned_score
                        + self._candidate_bonus(cleaned_text, field_type),
                    }
                )

            if not candidates:
                raise ValueError(
                    "No speech was detected. Please speak clearly and record again."
                )

            best = max(candidates, key=lambda item: float(item["score"]))
            information = best["information"]

            return {
                "status": "success",
                "transcript": str(best["text"]).strip(),
                "selected_audio": best["source"],
                "candidate_count": len(candidates),
                "candidate_transcripts": [
                    {
                        "source": item["source"],
                        "text": item["text"],
                        "score": round(float(item["score"]), 4),
                    }
                    for item in candidates
                ],
                "language": getattr(information, "language", language),
                "language_probability": float(
                    getattr(information, "language_probability", 0.0)
                ),
                "audio_duration_seconds": float(audio_metadata["duration_seconds"]),
                "sample_rate": int(audio_metadata["sample_rate"]),
                "noise_reduction_applied": bool(
                    audio_metadata["noise_reduction_applied"]
                ),
                "transcription_time_seconds": round(
                    time.perf_counter() - start_time, 3
                ),
                "model_size": self.model_size,
                "field_type": field_type,
                "prompt_used": bool(prompt),
            }

        finally:
            for temporary_path in (source_path, cleaned_path):
                if temporary_path and os.path.exists(temporary_path):
                    try:
                        os.remove(temporary_path)
                    except OSError:
                        pass
