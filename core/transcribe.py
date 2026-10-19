"""Abstração de backend de transcrição. Mesma interface para whisper.cpp (local/Mac)
e faster-whisper (nuvem/Linux) -- o núcleo de decupagem não sabe qual dos dois rodou."""
from __future__ import annotations
import subprocess
import shutil
from dataclasses import dataclass, field


@dataclass
class Word:
    text: str
    start: float
    end: float
    prob: float = 1.0


@dataclass
class Segment:
    text: str
    start: float
    end: float
    words: list[Word] = field(default_factory=list)


class TranscriptionBackend:
    def transcribe(self, audio_path: str, language: str = "pt") -> list[Segment]:
        raise NotImplementedError


class CloudFasterWhisperBackend(TranscriptionBackend):
    """Linux/nuvem. CPU, quantização int8 -- sem presumir GPU."""

    def __init__(self, model_size: str = "small", compute_type: str = "int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        self._model = None

    def _load(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device="cpu", compute_type=self.compute_type)
        return self._model

    def transcribe(self, audio_path: str, language: str = "pt") -> list[Segment]:
        model = self._load()
        segments, _info = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        out = []
        for seg in segments:
            words = [Word(w.word.strip(), w.start, w.end, getattr(w, "probability", 1.0)) for w in (seg.words or [])]
            out.append(Segment(seg.text.strip(), seg.start, seg.end, words))
        return out


class LocalWhisperCppBackend(TranscriptionBackend):
    """macOS/local. Chama o binário whisper.cpp (whisper-cli) compilado com suporte
    a Metal no M1, modelo multilíngue Small em GGUF. Não roda neste container Linux --
    código correto, não testado aqui (precisa do Mac)."""

    def __init__(self, binary_path: str = "whisper-cli", model_path: str = "models/ggml-small.bin"):
        self.binary_path = binary_path
        self.model_path = model_path

    def transcribe(self, audio_path: str, language: str = "pt") -> list[Segment]:
        if not shutil.which(self.binary_path):
            raise RuntimeError(
                f"'{self.binary_path}' não encontrado no PATH. Modo local requer whisper.cpp "
                "compilado no Mac (veja docs/INSTALACAO_MAC.md)."
            )
        cmd = [
            self.binary_path, "-m", self.model_path, "-f", audio_path,
            "-l", language, "-oj", "-ml", "1", "--output-file", "/tmp/whispercpp_out",
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        import json
        with open("/tmp/whispercpp_out.json", encoding="utf-8") as fh:
            data = json.load(fh)
        out = []
        for seg in data.get("transcription", []):
            words = [Word(w["text"].strip(), w["offsets"]["from"] / 1000, w["offsets"]["to"] / 1000)
                     for w in seg.get("words", [])] if "words" in seg else []
            out.append(Segment(seg["text"].strip(), seg["offsets"]["from"] / 1000, seg["offsets"]["to"] / 1000, words))
        return out
