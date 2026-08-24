from __future__ import annotations

import base64
import importlib
import os
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from eqo.speech.errors import STTTranscriptionError, STTUnavailable, TTSUnavailable
from eqo.speech.interfaces import AudioInput


class WhisperSTTProvider:
    """Adapter opcional; importa Whisper somente quando efetivamente utilizado."""

    def __init__(
        self,
        model_name: str = "tiny",
        language: str = "pt",
        *,
        model_loader: Callable[[str], Any] | None = None,
    ) -> None:
        self.model_name = model_name
        self.language = language
        self.model_loader = model_loader
        self._model: Any = None

    def transcribe(self, audio: AudioInput) -> str:
        if audio.media_type != "audio/wav":
            raise STTTranscriptionError("O adapter Whisper inicial aceita somente WAV.")
        model = self._load_model()
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary:
                temporary.write(audio.data)
                temporary_path = Path(temporary.name)
            result = model.transcribe(
                str(temporary_path), language=self.language, fp16=False
            )
            text = result.get("text") if isinstance(result, dict) else None
            if not isinstance(text, str) or not text.strip():
                raise STTTranscriptionError("O STT não retornou uma transcrição válida.")
            return text.strip()
        except STTTranscriptionError:
            raise
        except Exception as error:
            raise STTTranscriptionError("Falha ao transcrever o áudio local.") from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            loader = self.model_loader
            if loader is None:
                whisper = importlib.import_module("whisper")
                loader = whisper.load_model
            self._model = loader(self.model_name)
            return self._model
        except (ImportError, AttributeError) as error:
            raise STTUnavailable(
                "Whisper não está instalado; use texto ou configure outro STT."
            ) from error


Runner = Callable[..., subprocess.CompletedProcess[str]]


class WindowsSAPIProvider:
    """TTS local opcional via SAPI; o texto é passado como dado em base64."""

    SCRIPT = (
        "Add-Type -AssemblyName System.Speech; "
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$b=[Convert]::FromBase64String($env:EQO_TTS_TEXT); "
        "$t=[Text.Encoding]::UTF8.GetString($b); $s.Speak($t)"
    )

    def __init__(
        self,
        executable: str = "powershell.exe",
        timeout_seconds: float = 30.0,
        *,
        runner: Runner = subprocess.run,
    ) -> None:
        self.executable = executable
        self.timeout_seconds = timeout_seconds
        self.runner = runner

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        environment = os.environ.copy()
        environment["EQO_TTS_TEXT"] = base64.b64encode(text.encode()).decode()
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            result = self.runner(
                [
                    self.executable,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    self.SCRIPT,
                ],
                env=environment,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                creationflags=creation_flags,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise TTSUnavailable("O sintetizador de voz local está indisponível.") from error
        if result.returncode != 0:
            raise TTSUnavailable("O sintetizador de voz local falhou.")

