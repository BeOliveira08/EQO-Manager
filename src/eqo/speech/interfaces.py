from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AudioInput:
    data: bytes
    media_type: str = "audio/wav"

    def __post_init__(self) -> None:
        if not self.data:
            raise ValueError("O áudio não pode estar vazio.")


class STTProvider(Protocol):
    def transcribe(self, audio: AudioInput) -> str: ...


class TTSProvider(Protocol):
    def speak(self, text: str) -> None: ...


SpeechRecognizer = STTProvider
SpeechSynthesizer = TTSProvider
