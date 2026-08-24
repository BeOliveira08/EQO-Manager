class SpeechError(RuntimeError):
    pass


class STTUnavailable(SpeechError):
    pass


class STTTranscriptionError(SpeechError):
    pass


class TTSUnavailable(SpeechError):
    pass

