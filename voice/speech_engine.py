"""
Local speech-to-text engine used by Voice Incident Reporting.
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Any, Dict

from faster_whisper import WhisperModel


class SpeechRecognitionEngine:
    """
    Transcribe Streamlit microphone recordings with faster-whisper.
    """

    def __init__(
        self,
        model_size: str = "tiny.en",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:

        self.model_size = model_size

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "en",
    ) -> Dict[str, Any]:

        if not audio_bytes:

            raise ValueError(
                "The audio recording is empty."
            )

        start_time = time.perf_counter()
        temporary_path = None

        try:

            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as temporary_file:

                temporary_file.write(
                    audio_bytes
                )

                temporary_path = (
                    temporary_file.name
                )

            segments, information = (
                self.model.transcribe(
                    temporary_path,
                    language=language,
                    beam_size=3,
                    vad_filter=True,
                    condition_on_previous_text=False,
                )
            )

            transcript = " ".join(
                str(segment.text).strip()
                for segment in segments
                if str(segment.text).strip()
            ).strip()

            if not transcript:

                raise ValueError(
                    "No speech was detected. "
                    "Please record the response again."
                )

            return {
                "status":
                    "success",

                "transcript":
                    transcript,

                "language":
                    getattr(
                        information,
                        "language",
                        language,
                    ),

                "language_probability":
                    float(
                        getattr(
                            information,
                            "language_probability",
                            0.0,
                        )
                    ),

                "audio_duration_seconds":
                    float(
                        getattr(
                            information,
                            "duration",
                            0.0,
                        )
                    ),

                "transcription_time_seconds":
                    round(
                        time.perf_counter()
                        - start_time,
                        3,
                    ),

                "model_size":
                    self.model_size,
            }

        finally:

            if (
                temporary_path
                and os.path.exists(
                    temporary_path
                )
            ):

                os.remove(
                    temporary_path
                )
