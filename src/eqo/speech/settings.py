import os
from dataclasses import dataclass
from enum import StrEnum


class STTMode(StrEnum):
    DISABLED = "disabled"
    WHISPER = "whisper"


class TTSMode(StrEnum):
    DISABLED = "disabled"
    WINDOWS = "windows"


@dataclass(frozen=True, slots=True)
class SpeechSettings:
    stt_mode: STTMode = STTMode.DISABLED
    tts_mode: TTSMode = TTSMode.DISABLED
    whisper_model: str = "tiny"

    @classmethod
    def from_environment(cls) -> "SpeechSettings":
        raw_stt = os.getenv("EQO_STT_MODE", "disabled").casefold()
        raw_tts = os.getenv("EQO_TTS_MODE", "disabled").casefold()
        stt = STTMode(raw_stt) if raw_stt in {mode.value for mode in STTMode} else STTMode.DISABLED
        tts = TTSMode(raw_tts) if raw_tts in {mode.value for mode in TTSMode} else TTSMode.DISABLED
        return cls(
            stt_mode=stt,
            tts_mode=tts,
            whisper_model=os.getenv("EQO_WHISPER_MODEL", "tiny"),
        )
