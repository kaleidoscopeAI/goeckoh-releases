import threading
import time
from pathlib import Path
from queue import Empty

import numpy as np
import sherpa_onnx

from audio_driver import AudioManager, mic_queue, spk_queue
from mirror import MirrorNetwork
from neuro_magic import KineticState, PsychoacousticDSP
from physics import CrystallineHeart
from voice_crystal.crystal import VoiceCrystal

try:
    from plyer import accelerometer
except Exception:  # pragma: no cover - platform guard
    accelerometer = None


class GoeckohKernel(threading.Thread):
    """
    Fusion loop: mic -> ASR -> mirror -> affective gating -> TTS + entrainment.
    Integrated with high-fidelity VoiceCrystal for identity preservation and 
    prosody mirroring.
    """

    def __init__(self, user_id: str = "default_user", models_dir: str | Path | None = None, sample_rate: int = 16000):
        super().__init__(daemon=True)
        root = Path(__file__).resolve().parent.parent
        self.models_dir = Path(models_dir) if models_dir else root / "models"
        self.storage_dir = root / "storage"
        self.sample_rate = sample_rate

        self.heart = CrystallineHeart()
        self.mirror = MirrorNetwork()
        self.dsp = PsychoacousticDSP(sample_rate=sample_rate)
        self.kinetic = KineticState()
        
        # High-Fidelity Voice Crystal (Identity + AIM + Prosody)
        self.crystal = VoiceCrystal(
            user_id=user_id,
            models_dir=self.models_dir,
            storage_path=self.storage_dir,
            sample_rate=sample_rate
        )

        self.audio = AudioManager(sample_rate=sample_rate)
        self.running = False

        # Sherpa-ONNX models
        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=str(self.models_dir / "tokens.txt"),
            encoder=str(self.models_dir / "encoder.onnx"),
            decoder=str(self.models_dir / "decoder.onnx"),
            joiner=str(self.models_dir / "joiner.onnx"),
            num_threads=2,
            sample_rate=sample_rate,
            decoding_method="greedy_search",
        )
        self.stream = self.recognizer.create_stream()

        tts_cfg = sherpa_onnx.OfflineTtsVitsModelConfig(
            model=str(self.models_dir / "model.onnx"),
            tokens=str(self.models_dir / "tokens.txt"),
            lexicon=str(self.models_dir / "lexicon.txt"),
        )
        self.tts = sherpa_onnx.OfflineTts(
            sherpa_onnx.OfflineTtsModelConfig(vits=tts_cfg)
        )
        self.tts_speed = 1.0

        self.sensor_enabled = False

    def enable_sensors(self):
        if accelerometer is None:
            return
        try:
            accelerometer.enable()
            self.sensor_enabled = True
        except Exception as exc:
            print(f"[sensor] Accelerometer unavailable: {exc}")

    def disable_sensors(self):
        if accelerometer and self.sensor_enabled:
            try:
                accelerometer.disable()
            except Exception:
                pass
        self.sensor_enabled = False

    def start_kernel(self):
        if not self.running:
            self.running = True
            self.audio.start()
            self.enable_sensors()
            self.start()

    def stop_kernel(self):
        self.running = False
        self.disable_sensors()
        self.audio.stop()
        if self.is_alive():
            self.join(timeout=1.0)

    def _read_agitation(self) -> float:
        if not self.sensor_enabled:
            return 0.0
        try:
            val = accelerometer.acceleration
            if val and len(val) >= 3:
                return self.kinetic.update(val[0], val[1], val[2])
        except Exception:
            return 0.0
        return 0.0

    def _mix_output(self, voice: np.ndarray, stress_level: float, prosody: dict) -> np.ndarray:
        # 1. High-Fidelity Prosody Transfer from the original user utterance
        voice = self.crystal.apply_prosody(voice, prosody)
        
        # 2. Affective Filtering (Muffling/Softening based on stress)
        voice = self.dsp.apply_affective_filter(voice, stress_level)

        # 3. Binaural Entrainment (Subliminal state nudging)
        mode = "CALM" if stress_level > 0.5 else "FOCUS"
        binaural = self.dsp.generate_entrainment(
            duration_sec=len(voice) / self.sample_rate, target_state=mode
        )
        binaural_mono = binaural.reshape(-1, 2).mean(axis=1) if binaural.size else np.zeros_like(voice)
        mixed = voice + 0.1 * binaural_mono[: len(voice)]
        
        return mixed.astype(np.float32)

    def run(self):
        while self.running:
            agitation = self._read_agitation()
            try:
                raw_bytes = mic_queue.get(timeout=0.05)
            except Empty:
                continue

            # Process input samples
            if len(raw_bytes) % 4 == 0:
                f32 = np.frombuffer(raw_bytes, dtype=np.float32)
                if f32.size and np.max(np.abs(f32)) <= 2.0:
                    samples = f32
                else:
                    samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            rms = float(np.sqrt(np.mean(samples**2))) if samples.size else 0.0
            
            # 1. Real-time Prosody Extraction (Mapping current user emotion)
            current_prosody = self.crystal.extract_prosody(samples, self.sample_rate)

            self.stream.accept_waveform(self.sample_rate, samples)
            if self.recognizer.is_ready(self.stream):
                self.recognizer.decode_stream(self.stream)

            result = self.recognizer.get_result(self.stream)
            text = getattr(result, "text", "") if result else ""

            # 2. Adaptive Harvesting (AIM) - Continuous Voice Identity Learning
            if text and rms > 0.05:
                self.crystal.harvest_voice(samples, self.sample_rate)

            if text:
                t0 = time.perf_counter()
                
                # 3. Affective Mirroring (Linguistic Scaffolding with GCL-gating)
                gcl_snapshot = self.heart.gcl
                reflex = self.mirror.reflect(text, gcl=gcl_snapshot)
                
                # 4. Synthesize (Own-Voice Cloning using stable Identity)
                tts_audio = self.tts.generate(reflex, sid=0, speed=self.tts_speed)
                voice = np.array(tts_audio.samples, dtype=np.float32)
                latency_ms = (time.perf_counter() - t0) * 1000.0
            else:
                voice = np.zeros(0, dtype=np.float32)
                latency_ms = 0.0

            # 5. Physics-Based Safety Gating
            gcl, safe = self.heart.pulse(rms, latency_ms, agitation)

            if text and safe:
                stress_level = 1.0 - gcl
                mixed = self._mix_output(voice, stress_level, current_prosody)
                spk_queue.put(mixed)
                print(f"[loop] '{text}' -> '{reflex}' | GCL {gcl:.2f} | stress {stress_level:.2f}")
                self.stream = self.recognizer.create_stream()
            elif text:
                print(f"[safety] Muted output (GCL {gcl:.2f}, agitation {agitation:.2f})")

        self.audio.stop()
        self.disable_sensors()
