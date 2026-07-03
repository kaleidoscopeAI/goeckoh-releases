import os
import time
import queue
import threading
import logging
from pathlib import Path

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class SmartHarvester:
    """
    Mobile-safe voice facet harvester:
      - Pure NumPy DSP (no librosa/numba/scipy)
      - Bounded queue + worker thread (Pattern B)
      - Cheap-first gates (duration -> RMS -> flatness -> ZCR -> periodicity)
      - Optional VAD gate (adapter supports multiple sherpa interfaces)
      - Retention pruning (LRU by mtime)
    """

    def __init__(
        self,
        storage_path: Path,
        max_queue_size: int = 5,
        max_storage_bytes: int = 500 * 1024 * 1024,  # 500MB
        prune_every_n_writes: int = 25,
        vad=None,
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.queue = queue.Queue(maxsize=max_queue_size)
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        self.max_storage_bytes = int(max_storage_bytes)
        self.prune_every_n_writes = int(prune_every_n_writes)
        self._writes = 0

        self.vad = vad

        self.min_duration = 0.6
        self.max_duration = 8.0
        self.min_rms_db = -45.0
        self.max_flatness = 0.35
        self.max_zcr = 0.20
        self.min_periodicity = 0.40
        self.min_lag_hz = 50
        self.max_lag_hz = 500

    def submit_fragment(self, audio_chunk, sr=16000) -> bool:
        try:
            audio = np.array(audio_chunk, dtype=np.float32, copy=True)
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)
            self.queue.put_nowait((audio, int(sr)))
            return True
        except queue.Full:
            return False

    def stop(self):
        self.running = False
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            pass
        self.worker_thread.join()

    def _worker_loop(self):
        while self.running:
            try:
                item = self.queue.get(timeout=1.0)
                if item is None:
                    break
                audio, sr = item
                try:
                    self._analyze_and_save(audio, sr)
                except Exception as e:
                    logger.exception(f"Harvesting error: {e}")
                finally:
                    self.queue.task_done()
            except queue.Empty:
                continue

    def _analyze_and_save(self, audio: np.ndarray, sr: int):
        # 0) DC offset removal
        audio = audio - float(np.mean(audio))

        # 1) Duration gate
        duration = len(audio) / sr
        if not (self.min_duration <= duration <= self.max_duration):
            return

        # 2) RMS gate (pre-normalization)
        rms = float(np.sqrt(np.mean(audio * audio)))
        rms_db = 20.0 * np.log10(rms + 1e-9)
        if rms_db < self.min_rms_db:
            return

        # 2.5) Optional VAD gate (robust adapter)
        if self.vad is not None:
            if not self._vad_is_speech(audio, sr):
                return

        # 3) Peak normalize for stable features
        peak = float(np.max(np.abs(audio)))
        if peak > 0:
            audio = audio / peak

        # 4) Spectral flatness
        flatness = self._spectral_flatness_fft(audio)
        if flatness > self.max_flatness:
            return

        # 5) ZCR
        zcr = self._zcr(audio)
        if zcr > self.max_zcr:
            return

        # 6) Periodicity proxy
        periodicity = self._periodicity_proxy(audio, sr)
        if periodicity < self.min_periodicity:
            return

        # 7) Conditional dithering + limiter
        if duration < 1.5:
            dither_sigma = 10 ** (-65 / 20)
            audio = audio + np.random.normal(0.0, dither_sigma, size=len(audio)).astype(np.float32)
            peak2 = float(np.max(np.abs(audio)))
            if peak2 > 0.99:
                audio = audio * (0.99 / peak2)

        # 8) Commit
        filename = self.storage_path / f"facet_{int(time.time() * 1000)}.wav"
        sf.write(str(filename), audio, sr)

        # 9) Prune occasionally
        self._writes += 1
        if self._writes % self.prune_every_n_writes == 0:
            self._prune_storage()

        logger.info(
            f"Harvested {filename.name} | rms={rms_db:.1f}, flat={flatness:.2f}, zcr={zcr:.2f}, per={periodicity:.2f}"
        )

    # ---------- VAD adapter ----------
    def _vad_is_speech(self, audio: np.ndarray, sr: int) -> bool:
        """
        Supports common patterns:
          - vad.is_speech(float32_audio, sr)
          - vad.is_speech(int16_pcm, sr)
          - vad(audio, sr)
        If VAD errors, default to True (never crash harvester).
        """
        try:
            # Try float32 normalized first
            a = audio
            peak = float(np.max(np.abs(a)))
            if peak > 0:
                a = a / peak

            fn = getattr(self.vad, "is_speech", None)
            if callable(fn):
                try:
                    return bool(fn(a.astype(np.float32), sr))
                except TypeError:
                    pcm = np.clip(a * 32767.0, -32768, 32767).astype(np.int16)
                    return bool(fn(pcm, sr))

            # callable vad itself
            try:
                return bool(self.vad(a.astype(np.float32), sr))
            except TypeError:
                pcm = np.clip(a * 32767.0, -32768, 32767).astype(np.int16)
                return bool(self.vad(pcm, sr))

        except Exception:
            return True

    # ---------- DSP helpers ----------
    def _spectral_flatness_fft(self, audio: np.ndarray) -> float:
        n = min(len(audio), 2048)
        if n < 256:
            return 1.0

        x = audio[:n] * np.hanning(n).astype(np.float32)
        spec = np.fft.rfft(x)
        psd = (spec.real * spec.real + spec.imag * spec.imag) + 1e-12

        gmean = float(np.exp(np.mean(np.log(psd))))
        amean = float(np.mean(psd))
        return float(gmean / (amean + 1e-12))

    def _zcr(self, audio: np.ndarray) -> float:
        s = np.sign(audio)
        s[s == 0] = 1
        return float(np.mean(np.abs(np.diff(s))) * 0.5)

    def _periodicity_proxy(self, audio: np.ndarray, sr: int) -> float:
        n = min(len(audio), 4096)
        if n < 512:
            return 0.0

        x = audio[:n].astype(np.float32)
        x = x - float(np.mean(x))
        r0 = float(np.dot(x, x)) + 1e-12

        m = 1
        while m < 2 * n:
            m <<= 1

        X = np.fft.rfft(x, n=m)
        S = (X.real * X.real + X.imag * X.imag)
        corr = np.fft.irfft(S, n=m)[:n].astype(np.float32)

        min_lag = int(sr / self.max_lag_hz)
        max_lag = int(sr / self.min_lag_hz)
        if max_lag <= min_lag or max_lag >= len(corr):
            return 0.0

        peak = float(np.max(corr[min_lag:max_lag]))
        return float(peak / r0)

    # ---------- pruning ----------
    def _prune_storage(self):
        files = [p for p in self.storage_path.glob("facet_*.wav") if p.is_file()]
        if not files:
            return

        files.sort(key=lambda p: p.stat().st_mtime)
        total = sum(p.stat().st_size for p in files)
        if total <= self.max_storage_bytes:
            return

        target = int(self.max_storage_bytes * 0.90)
        for p in files:
            try:
                size = p.stat().st_size
                p.unlink()
                total -= size
            except Exception:
                pass
            if total <= target:
                break
