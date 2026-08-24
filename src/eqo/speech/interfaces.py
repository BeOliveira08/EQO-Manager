from typing import Protocol


class SpeechRecognizer(Protocol):
    def transcribe(self, audio: bytes) -> str: ...


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str) -> bytes: ...

