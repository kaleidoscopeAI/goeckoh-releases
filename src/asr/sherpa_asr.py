import numpy as np
import sherpa_onnx


class SherpaASR:
    """
    Mobile-safe Sherpa-ONNX ASR adapter.

    Expected model layout (after ensure_assets_extracted):
      model_dir/
        tokens.txt
        encoder.onnx
        decoder.onnx
        joiner.onnx
    """

    def __init__(self, model_dir: str, sample_rate: int = 16000):
        self.sample_rate = int(sample_rate)
        self.recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f"{model_dir}/encoder.onnx",
            decoder=f"{model_dir}/decoder.onnx",
            joiner=f"{model_dir}/joiner.onnx",
            tokens=f"{model_dir}/tokens.txt",
            sample_rate=self.sample_rate,
            feature_dim=80,
            decoding_method="greedy_search",
            num_threads=2,
            provider="cpu",
        )

    def transcribe(self, audio: np.ndarray, sr: int) -> str:
        """
        audio: float32 mono [-1,1]
        sr: sample rate (must be 16k)
        """
        if sr != self.sample_rate or audio is None or len(audio) == 0:
            return ""

        audio = np.asarray(audio, dtype=np.float32)

        stream = self.recognizer.create_stream()
        stream.accept_waveform(self.sample_rate, audio)
        self.recognizer.decode_stream(stream)
        text = stream.result.text
        return text.strip()
