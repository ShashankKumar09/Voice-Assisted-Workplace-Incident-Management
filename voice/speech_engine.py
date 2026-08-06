"""Reliable local speech-to-text engine for Voice Incident Reporting."""
from __future__ import annotations

import os
import re
import tempfile
import time
from typing import Any, Dict, List, Tuple

import noisereduce as nr
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel


DIGIT_WORDS = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "two": "2", "to": "2", "too": "2",
    "three": "3", "four": "4", "for": "4",
    "five": "5", "six": "6", "seven": "7",
    "eight": "8", "ate": "8", "nine": "9",
}


class SpeechRecognitionEngine:
    """Transcribe Streamlit microphone recordings with faster-whisper."""

    SHORT_FIELD_TYPES = {
        "identifier", "digits", "latitude", "longitude",
        "date", "yes_no", "federal_state",
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

        audio_array = np.nan_to_num(audio_array, nan=0.0, posinf=0.0, neginf=0.0)
        audio_array -= float(np.mean(audio_array))
        duration_seconds = len(audio_array) / float(sample_rate)

        if duration_seconds < 0.35:
            raise ValueError("The recording is too short. Please record again.")

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
                prop_decrease=0.25,
            )
            if reduced is not None and len(reduced) == len(audio_array):
                reduced = np.asarray(reduced, dtype=np.float32)
                reduced_rms = float(np.sqrt(np.mean(np.square(reduced))))
                if reduced_rms >= rms * 0.60:
                    audio_array = reduced
                    noise_reduction_applied = True
        except Exception:
            pass

        peak = float(np.max(np.abs(audio_array)))
        if peak > 0:
            audio_array = np.clip(audio_array * (0.88 / peak), -1.0, 1.0)

        sf.write(output_path, audio_array.astype(np.float32), sample_rate, subtype="PCM_16")
        return {
            "sample_rate": int(sample_rate),
            "duration_seconds": float(duration_seconds),
            "noise_reduction_applied": noise_reduction_applied,
        }

    def _transcribe_path(
        self,
        path: str,
        *,
        language: str,
        prompt: str | None,
        field_type: str,
    ) -> Tuple[str, Any, float]:
        short_field = field_type in self.SHORT_FIELD_TYPES
        segments, information = self.model.transcribe(
            path,
            language=language,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 350,
                "speech_pad_ms": 250,
            },
            condition_on_previous_text=False,
            word_timestamps=False,
            initial_prompt=prompt or None,
            no_speech_threshold=0.55,
            log_prob_threshold=-0.8,
            compression_ratio_threshold=1.8 if short_field else 2.4,
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
        avg_no_speech = sum(no_speech_probs) / len(no_speech_probs) if no_speech_probs else 1.0
        return transcript, information, avg_logprob - avg_no_speech

    @staticmethod
    def _is_repetitive(text: str) -> bool:
        compact = re.sub(r"\s+", "", text.lower())
        if re.search(r"(.{1,8})\1{4,}", compact):
            return True
        chars = [char for char in compact if char.isalnum()]
        if len(chars) >= 25:
            most_common = max(chars.count(char) for char in set(chars))
            return most_common / len(chars) > 0.55
        return False

    @staticmethod
    def _tokens(value: str) -> List[str]:
        cleaned = value.lower().strip()
        cleaned = (
            cleaned.replace("–", "-")
            .replace("—", "-")
            .replace("−", "-")
        )
        return re.findall(r"[a-z]+|\d+|[-_/.]", cleaned)

    @classmethod
    def _normalize_short_value(cls, value: str, field_type: str) -> str:
        tokens = cls._tokens(value)
        output: List[str] = []
        index = 0

        while index < len(tokens):
            token = tokens[index]
            if token in {"double", "triple"}:
                repeat_count = 2 if token == "double" else 3
                next_index = index + 1
                while next_index < len(tokens) and tokens[next_index] in {"-", "_", "/"}:
                    next_index += 1
                if next_index < len(tokens):
                    next_token = tokens[next_index]
                    digit = DIGIT_WORDS.get(next_token)
                    if digit is None and next_token.isdigit() and len(next_token) == 1:
                        digit = next_token
                    if digit is not None:
                        output.append(digit * repeat_count)
                        index = next_index + 1
                        continue

            if token in DIGIT_WORDS:
                output.append(DIGIT_WORDS[token])
            elif token.isdigit():
                output.append(token)
            elif token in {"point", "dot", "."}:
                output.append(".")
            elif token in {"minus", "negative", "-"}:
                if field_type in {"latitude", "longitude"} and not output:
                    output.append("-")
                elif field_type == "identifier":
                    output.append("-")
            elif token in {"_", "/"} and field_type == "identifier":
                output.append(token)
            elif field_type == "identifier" and token.isalpha():
                output.append(token.upper())
            index += 1

        normalized = "".join(output)
        if field_type == "digits":
            return re.sub(r"\D", "", normalized)
        if field_type in {"latitude", "longitude"}:
            normalized = re.sub(r"(?!^)-", "", normalized)
            normalized = re.sub(r"\.(?=.*\.)", "", normalized)
            return normalized
        if field_type == "identifier" and re.fullmatch(r"[0-9._/-]+", normalized):
            return re.sub(r"\D", "", normalized)
        return normalized or value.strip()

    @classmethod
    def _validate_candidate(
        cls,
        text: str,
        field_type: str,
        duration_seconds: float,
    ) -> bool:
        value = text.strip()
        if not value or cls._is_repetitive(value):
            return False

        normalized = cls._normalize_short_value(value, field_type)
        compact = re.sub(r"\s+", "", normalized)
        if field_type in cls.SHORT_FIELD_TYPES:
            if len(compact) > max(24, int(duration_seconds * 12)):
                return False

        if field_type == "identifier":
            return 1 <= len(re.sub(r"[^A-Za-z0-9_-]", "", normalized)) <= 24
        if field_type == "digits":
            return 1 <= len(re.sub(r"\D", "", normalized)) <= 12
        if field_type in {"latitude", "longitude"}:
            try:
                numeric = float(normalized)
            except ValueError:
                return False
            minimum, maximum = (-90.0, 90.0) if field_type == "latitude" else (-180.0, 180.0)
            return minimum <= numeric <= maximum
        if field_type == "yes_no":
            return bool(re.search(r"\b(?:yes|yeah|yep|no|nope)\b", value.lower()))
        if field_type == "federal_state":
            lower = value.lower()
            return "federal" in lower or bool(re.search(r"\bstate\b", lower))
        return True

    @staticmethod
    def _candidate_bonus(text: str, field_type: str) -> float:
        if not text:
            return -100.0
        bonus = 0.0
        if field_type in {"identifier", "digits", "latitude", "longitude"}:
            bonus += min(len(re.findall(r"\d", text)), 12) * 0.10
        elif field_type == "yes_no":
            bonus += 1.0 if re.search(r"\b(?:yes|no)\b", text.lower()) else 0.0
        elif field_type == "federal_state":
            bonus += 1.0 if re.search(r"\b(?:federal|state)\b", text.lower()) else 0.0
        elif field_type == "narrative":
            bonus += min(len(text.split()), 30) * 0.025
        return bonus

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "en",
        prompt: str | None = None,
        field_type: str = "text",
    ) -> Dict[str, Any]:
        if not audio_bytes:
            raise ValueError("The audio recording is empty.")

        start_time = time.perf_counter()
        source_path: str | None = None
        cleaned_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as source_file:
                source_file.write(audio_bytes)
                source_path = source_file.name
            with tempfile.NamedTemporaryFile(suffix="_clean.wav", delete=False) as cleaned_file:
                cleaned_path = cleaned_file.name

            metadata = self._prepare_audio(source_path, cleaned_path)
            candidates: List[Dict[str, Any]] = []

            for source_name, path in (("original", source_path), ("cleaned", cleaned_path)):
                text, information, score = self._transcribe_path(
                    path,
                    language=language,
                    prompt=prompt,
                    field_type=field_type,
                )
                normalized_text = (
                    self._normalize_short_value(text, field_type)
                    if field_type in self.SHORT_FIELD_TYPES
                    else text.strip()
                )
                if normalized_text and self._validate_candidate(
                    normalized_text,
                    field_type,
                    float(metadata["duration_seconds"]),
                ):
                    candidates.append(
                        {
                            "source": source_name,
                            "text": normalized_text,
                            "information": information,
                            "score": score + self._candidate_bonus(normalized_text, field_type),
                        }
                    )

            if not candidates:
                raise ValueError(
                    "The recording could not be recognized reliably. Please record again and speak slowly."
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
                "language_probability": float(getattr(information, "language_probability", 0.0)),
                "audio_duration_seconds": float(metadata["duration_seconds"]),
                "sample_rate": int(metadata["sample_rate"]),
                "noise_reduction_applied": bool(metadata["noise_reduction_applied"]),
                "transcription_time_seconds": round(time.perf_counter() - start_time, 3),
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
