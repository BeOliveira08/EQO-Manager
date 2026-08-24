import base64
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from eqo.speech.adapters import WhisperSTTProvider, WindowsSAPIProvider
from eqo.speech.errors import STTTranscriptionError, TTSUnavailable
from eqo.speech.interfaces import AudioInput


class FakeWhisperModel:
    def __init__(self) -> None:
        self.path: Path | None = None

    def transcribe(self, path: str, **_options: object) -> dict[str, str]:
        self.path = Path(path)
        assert self.path.exists()
        return {"text": "  minhas tarefas  "}


def test_whisper_adapter_is_lazy_and_removes_temporary_audio() -> None:
    model = FakeWhisperModel()
    loaded: list[str] = []

    def loader(name: str) -> FakeWhisperModel:
        loaded.append(name)
        return model

    provider = WhisperSTTProvider("tiny", model_loader=loader)
    assert provider.transcribe(AudioInput(b"RIFFfake")) == "minhas tarefas"
    assert loaded == ["tiny"]
    assert model.path is not None
    assert not model.path.exists()


def test_whisper_rejects_unsupported_audio_type() -> None:
    with pytest.raises(STTTranscriptionError, match="WAV"):
        WhisperSTTProvider(model_loader=lambda _name: FakeWhisperModel()).transcribe(
            AudioInput(b"data", "audio/mp3")
        )


def test_windows_tts_passes_text_as_data_not_powershell_code() -> None:
    captured: dict[str, object] = {}

    def runner(args: list[str], **kwargs: object) -> CompletedProcess[str]:
        captured["args"] = args
        captured["env"] = kwargs["env"]
        return CompletedProcess(args, 0, "", "")

    text = "Olá; Remove-Item não é instrução"
    WindowsSAPIProvider(runner=runner).speak(text)
    environment = captured["env"]
    encoded = environment["EQO_TTS_TEXT"]  # type: ignore[index]
    assert base64.b64decode(encoded).decode() == text
    assert text not in " ".join(captured["args"])  # type: ignore[arg-type]


def test_windows_tts_failure_is_explicit() -> None:
    def runner(args: list[str], **_kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(args, 1, "", "erro")

    with pytest.raises(TTSUnavailable):
        WindowsSAPIProvider(runner=runner).speak("teste")

