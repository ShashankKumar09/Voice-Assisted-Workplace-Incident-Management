"""
Local speech-to-text engine used by Voice Incident Reporting.

Features:
- WAV validation
- mono conversion
- peak normalization
- background-noise reduction
- faster-whisper transcription
- VAD-based silence filtering
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import noisereduce as nr
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel


class SpeechRecognitionEngine:
    """Transcribe Streamlit microphone recordings with faster-whisper."""

    def __init__(
        self,
        model_size: str = "tiny.en",
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
    def _prepare_audio(
        source_path: str,
        output_path: str,
    ) -> Dict[str, Any]:
        """
        Convert to mono, remove DC offset, reduce steady background noise,
        normalize volume and write a clean WAV file.
        """
        audio, sample_rate = sf.read(
            source_path,
            always_2d=False,
            dtype="float32",
        )

        if audio is None or np.size(audio) == 0:
            raise ValueError("The audio recording is empty.")

        audio_array = np.asarray(audio, dtype=np.float32)

        if audio_array.ndim == 2:
            audio_array = np.mean(
                audio_array,
                axis=1,
                dtype=np.float32,
            )

        audio_array = np.nan_to_num(
            audio_array,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        # Remove DC offset.
        audio_array = audio_array - float(
            np.mean(audio_array)
        )

        duration_seconds = (
            len(audio_array) / float(sample_rate)
        )

        if duration_seconds < 0.35:
            raise ValueError(
                "The recording is too short. "
                "Please record the response again."
            )

        # Noise reduction works best when the recording contains a little
        # ambient sound. If it fails, continue with the original waveform.
        noise_reduction_applied = False

        try:
            reduced_audio = nr.reduce_noise(
                y=audio_array,
                sr=sample_rate,
                stationary=True,
                prop_decrease=0.75,
                n_std_thresh_stationary=1.5,
            )

            if (
                reduced_audio is not None
                and len(reduced_audio) == len(audio_array)
            ):
                audio_array = np.asarray(
                    reduced_audio,
                    dtype=np.float32,
                )
                noise_reduction_applied = True

        except Exception:
            noise_reduction_applied = False

        # Normalize safely without amplifying silence excessively.
        peak = float(
            np.max(
                np.abs(audio_array)
            )
        )

        if peak < 1e-5:
            raise ValueError(
                "No usable speech was detected. "
                "Please record the response again."
            )

        target_peak = 0.92
        audio_array = np.clip(
            audio_array * (target_peak / peak),
            -1.0,
            1.0,
        ).astype(np.float32)

        sf.write(
            output_path,
            audio_array,
            sample_rate,
            subtype="PCM_16",
        )

        return {
            "sample_rate": int(sample_rate),
            "duration_seconds": float(duration_seconds),
            "noise_reduction_applied": noise_reduction_applied,
        }

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "en",
        prompt: str | None = None,
    ) -> Dict[str, Any]:
        """Clean and transcribe a WAV recording supplied as bytes.

        ``prompt`` supplies field-specific context to Whisper without changing
        the returned transcript format.
        """

        if not audio_bytes:
            raise ValueError(
                "The audio recording is empty."
            )

        start_time = time.perf_counter()
        source_path: str | None = None
        cleaned_path: str | None = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as source_file:
                source_file.write(audio_bytes)
                source_path = source_file.name

            with tempfile.NamedTemporaryFile(
                suffix="_clean.wav",
                delete=False,
            ) as cleaned_file:
                cleaned_path = cleaned_file.name

            audio_metadata = self._prepare_audio(
                source_path=source_path,
                output_path=cleaned_path,
            )

            segments, information = self.model.transcribe(
                cleaned_path,
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
            )

            transcript_parts = []

            for segment in segments:
                segment_text = str(
                    segment.text
                ).strip()

                if segment_text:
                    transcript_parts.append(
                        segment_text
                    )

            transcript = " ".join(
                transcript_parts
            ).strip()

            if not transcript:
                raise ValueError(
                    "No speech was detected. "
                    "Please move closer to the microphone "
                    "and record the response again."
                )

            return {
                "status": "success",
                "transcript": transcript,
                "language": getattr(
                    information,
                    "language",
                    language,
                ),
                "language_probability": float(
                    getattr(
                        information,
                        "language_probability",
                        0.0,
                    )
                ),
                "audio_duration_seconds": float(
                    audio_metadata[
                        "duration_seconds"
                    ]
                ),
                "sample_rate": int(
                    audio_metadata[
                        "sample_rate"
                    ]
                ),
                "noise_reduction_applied": bool(
                    audio_metadata[
                        "noise_reduction_applied"
                    ]
                ),
                "transcription_time_seconds": round(
                    time.perf_counter() - start_time,
                    3,
                ),
                "model_size": self.model_size,
                "prompt_used": bool(prompt),
            }

        finally:
            for temporary_path in [
                source_path,
                cleaned_path,
            ]:
                if (
                    temporary_path
                    and os.path.exists(
                        temporary_path
                    )
                ):
                    os.remove(
                        temporary_path
                    )
