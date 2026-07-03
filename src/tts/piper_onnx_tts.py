import numpy as np


class PiperONNXTTS:
    """
    Piper-style ONNX TTS adapter.

    Contract:
      - synthesize(text, sr) -> float32 mono waveform
      - synthesize_stream(text, sr, chunk_frames) -> yields float32 chunks
    """

    def __init__(self, model_path: str, sample_rate: int = 22050):
        self.model_path = model_path
        self.sample_rate = int(sample_rate)

        try:
            import onnxruntime as ort
        except Exception as e:  # pragma: no cover - runtime guard
            raise RuntimeError(
                "onnxruntime is required for PiperONNXTTS. "
                "Package a wheel/recipe for Android."
            ) from e

        self._ort = ort
        self.sess = ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
        self.input_names = [i.name for i in self.sess.get_inputs()]
        self.output_names = [o.name for o in self.sess.get_outputs()]
        self._warmed = False

    def warmup(self):
        self._warmed = True

    def text_to_ids(self, text: str) -> np.ndarray:
        """
        Convert text -> int64 token/phoneme ids expected by your ONNX model.
        Stubbed here; wire your phonemizer/tokenizer for your export.
        """
        raise NotImplementedError("Implement text->ids for your ONNX TTS export.")

    def synthesize(self, text: str, sr: int = None) -> np.ndarray:
        if not text:
            return np.zeros(0, dtype=np.float32)

        if sr is None:
            sr = self.sample_rate
        if int(sr) != self.sample_rate:
            raise ValueError(f"TTS model sr={self.sample_rate}, requested sr={sr}")

        ids = self.text_to_ids(text)  # [1, T] int64
        feeds = {}
        if "input_ids" in self.input_names:
            feeds["input_ids"] = ids
        elif "tokens" in self.input_names:
            feeds["tokens"] = ids
        else:
            raise RuntimeError(f"Unknown ONNX input names: {self.input_names}")

        if "input_lengths" in self.input_names:
            feeds["input_lengths"] = np.array([ids.shape[1]], dtype=np.int64)

        outs = self.sess.run(self.output_names, feeds)

        wav = None
        for o in outs:
            if isinstance(o, np.ndarray) and o.dtype in (np.float32, np.float64) and o.ndim >= 1:
                wav = o
                break
        if wav is None:
            raise RuntimeError("No waveform-like output found from ONNX session.")

        wav = np.asarray(wav).reshape(-1).astype(np.float32)
        peak = float(np.max(np.abs(wav))) if wav.size else 0.0
        if peak > 0.99:
            wav *= 0.99 / peak
        return wav

    def synthesize_stream(self, text: str, sr: int = None, chunk_frames: int = 320):
        wav = self.synthesize(text, sr=sr)
        if wav.size == 0:
            return
        chunk_frames = int(chunk_frames)
        i = 0
        n = len(wav)
        while i < n:
            yield wav[i : i + chunk_frames]
            i += chunk_frames
