import os
import time
import math
import re
import threading
import queue
from pathlib import Path

import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Ellipse
from kivy.core.window import Window

# --- CONFIGURATION ---
MODEL_PATH = "models"
SAMPLE_RATE = 16000


# -------------------------------------------------------------------------
# 1. THE CRYSTALLINE HEART (Physics Engine)
# -------------------------------------------------------------------------
class CrystallineHeart:
    """Affective safety gating."""

    def __init__(self):
        self.gcl = 1.0
        self.stress_heat = 0.0
        self.last_tick = time.time()

    def pulse(self, audio_rms: float, kinetic_energy: float) -> float:
        now = time.time()
        dt = max(1e-3, now - self.last_tick)
        self.last_tick = now

        stress_influx = (audio_rms * 2.0) + (kinetic_energy * 3.0)
        cooling = 0.5 * dt
        self.stress_heat = max(0.0, self.stress_heat + stress_influx - cooling)

        self.gcl = 1.0 / (1.0 + (self.stress_heat / 5.0))
        return self.gcl

    def is_safe(self) -> bool:
        return self.gcl > 0.4


# -------------------------------------------------------------------------
# 2. THE MIRROR (Logic Core)
# -------------------------------------------------------------------------
class MirrorNetwork:
    """Deterministic second-person to first-person reflection."""

    def __init__(self):
        self.rules = [
            (r"\b(are|Are)\s+you\b", "am I"),
            (r"\b(y|Y)ou\b", "I"),
            (r"\b(y|Y)our\b", "my"),
            (r"\b(m|M)e\b", "myself"),
        ]

    def reflect(self, text: str) -> str:
        if not text:
            return ""
        for pattern, replacement in self.rules:
            text = re.sub(pattern, replacement, text)
        return text.strip().capitalize()


# -------------------------------------------------------------------------
# 3. HARDWARE ABSTRACTION LAYER (Audio Drivers)
# -------------------------------------------------------------------------
audio_queue_in: queue.Queue[bytes] = queue.Queue()
audio_queue_out: queue.Queue[bytes] = queue.Queue()


class AudioBridge:
    """Auto-switches between PyJnius (Android) and sounddevice (desktop)."""

    def __init__(self):
        self.running = False
        self.stream = None

    def start(self):
        self.running = True
        if platform == "android":
            self._start_android()
        else:
            self._start_desktop()

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def _start_desktop(self):
        import sounddevice as sd

        def callback(indata, outdata, frames, time_info, status):
            if status:
                print(f"[audio] status {status}")
            if not self.running:
                raise sd.CallbackStop()

            audio_queue_in.put(bytes(indata))

            outdata.fill(0)
            try:
                data = audio_queue_out.get_nowait()
                arr = np.frombuffer(data, dtype=np.int16)
                if arr.size:
                    arr = arr.reshape(-1, 1)
                    length = min(frames, arr.shape[0])
                    outdata[:length, 0] = arr[:length, 0]
            except queue.Empty:
                pass

        self.stream = sd.Stream(
            callback=callback,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        self.stream.start()

    def _start_android(self):
        from jnius import autoclass

        AudioRecord = autoclass("android.media.AudioRecord")
        AudioTrack = autoclass("android.media.AudioTrack")
        AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
        AudioFormat = autoclass("android.media.AudioFormat")
        AudioManager = autoclass("android.media.AudioManager")

        def android_loop():
            min_buf = AudioRecord.getMinBufferSize(
                SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT
            )
            recorder = AudioRecord(
                AudioSource.MIC,
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                min_buf * 2,
            )
            player = AudioTrack(
                AudioManager.STREAM_MUSIC,
                SAMPLE_RATE,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                min_buf * 2,
                AudioTrack.MODE_STREAM,
            )

            recorder.startRecording()
            player.play()

            buf = bytearray(min_buf)
            while self.running:
                recorder.read(buf, 0, min_buf)
                audio_queue_in.put(bytes(buf))
                try:
                    out_bytes = audio_queue_out.get_nowait()
                    player.write(out_bytes, 0, len(out_bytes))
                except queue.Empty:
                    pass

            recorder.stop()
            recorder.release()
            player.stop()
            player.release()

        threading.Thread(target=android_loop, daemon=True).start()


# -------------------------------------------------------------------------
# 4. NEURAL PROCESSING KERNEL (Sherpa-ONNX)
# -------------------------------------------------------------------------
def _resample_linear(audio: np.ndarray, src_rate: int, target_rate: int) -> np.ndarray:
    if src_rate == target_rate or audio.size == 0:
        return audio.astype(np.float32)
    duration = audio.shape[0] / float(src_rate)
    tgt_len = int(duration * target_rate)
    src_times = np.linspace(0.0, duration, num=audio.shape[0], endpoint=False)
    tgt_times = np.linspace(0.0, duration, num=tgt_len, endpoint=False)
    return np.interp(tgt_times, src_times, audio).astype(np.float32)


class NeuroKernel(threading.Thread):
    def __init__(self, ui_callback):
        super().__init__(daemon=True)
        self.ui_cb = ui_callback
        self.audio = AudioBridge()
        self.heart = CrystallineHeart()
        self.mirror = MirrorNetwork()
        self.running = True

        self.accel = None
        try:
            from plyer import accelerometer

            accelerometer.enable()
            self.accel = accelerometer
        except Exception:
            print("[sensor] Accelerometer unavailable")

        base = Path(__file__).resolve().parent / MODEL_PATH
        base = str(base) + os.sep

        import sherpa_onnx

        try:
            self.asr = sherpa_onnx.OnlineRecognizer.from_transducer(
                tokens=base + "tokens.txt",
                encoder=base + "encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
                decoder=base + "decoder.onnx",
                joiner=base + "joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx",
                num_threads=1,
                provider="cpu",
                decoding_method="greedy_search",
            )
            self.stream = self.asr.create_stream()

            # self.tts = sherpa_onnx.OfflineTts(
            #     config=sherpa_onnx.OfflineTtsConfig(
            #         model=sherpa_onnx.OfflineTtsModelConfig(
            #             vits=sherpa_onnx.OfflineTtsVitsModelConfig(
            #                 model=base + "tts_model.onnx",
            #                 tokens=base + "tokens.txt",
            #                 lexicon=base + "lexicon.txt",
            #             )
            #         )
            #     )
            # )
            self.tts = None
            self.models_loaded = True
        except Exception as exc:
            print(f"[models] Load failed: {exc}")
            self.models_loaded = False

    def run(self):
        if not self.models_loaded:
            return

        self.audio.start()

        while self.running:
            kinetic = 0.0
            if self.accel:
                try:
                    val = self.accel.acceleration
                    if val and len(val) >= 3:
                        kinetic = (abs(val[0]) + abs(val[1]) + abs(val[2]) - 9.81)
                        kinetic = max(0.0, min(1.0, abs(kinetic) / 10.0))
                except Exception:
                    kinetic = 0.0

            try:
                raw = audio_queue_in.get(timeout=0.05)
            except queue.Empty:
                continue

            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            rms = float(np.sqrt(np.mean(samples**2))) if samples.size else 0.0

            gcl = self.heart.pulse(rms, kinetic)
            is_safe = self.heart.is_safe()
            Clock.schedule_once(lambda dt, g=gcl, s=is_safe: self.ui_cb(g, s), 0)

            if not is_safe:
                continue

            try:
                self.stream.accept_waveform(SAMPLE_RATE, samples)
                while self.asr.is_ready(self.stream):
                    self.asr.decode_stream(self.stream)

                res = self.asr.get_result(self.stream)
                text = getattr(res, "text", "") if res else ""

                if text and len(text) > 2:
                    # corrected = self.mirror.reflect(text)
                    # audio_obj = self.tts.generate(corrected, sid=0, speed=1.1)
                    # audio_np = np.array(audio_obj.samples, dtype=np.float32)
                    # audio_np = _resample_linear(
                    #     audio_np, getattr(audio_obj, "sample_rate", SAMPLE_RATE), SAMPLE_RATE
                    # )
                    # pcm = (audio_np * 32767.0).astype(np.int16).tobytes()
                    # audio_queue_out.put(pcm)
                    self.asr.reset(self.stream)
            except Exception as exc:
                print(f"[loop] error: {exc}")

        self.audio.stop()


# -------------------------------------------------------------------------
# 5. THE INTERFACE (Kivy)
# -------------------------------------------------------------------------
class GoeckohUI(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        layout = BoxLayout(orientation="vertical", padding=50, spacing=20)

        self.orb_area = BoxLayout(size_hint=(1, 0.6))
        with self.orb_area.canvas:
            self.orb_color = Color(0.0, 1.0, 0.0, 1)
            self.orb = Ellipse(size=(300, 300))
        layout.add_widget(self.orb_area)

        self.status = Label(text="Initializing Exocortex...", font_size="20sp", size_hint=(1, 0.2))
        layout.add_widget(self.status)

        self.toggle_btn = Button(text="Stop", size_hint=(1, 0.2))
        self.toggle_btn.bind(on_press=self.toggle_kernel)
        layout.add_widget(self.toggle_btn)

        return layout

    def on_start(self):
        self.kernel = NeuroKernel(self.update_orb)
        self.kernel.start()
        self.active = True

    def toggle_kernel(self, _instance):
        if self.active:
            self.kernel.running = False
            self.kernel.audio.stop()
            self.active = False
            self.status.text = "Stopped"
            self.toggle_btn.text = "Start"
        else:
            self.kernel = NeuroKernel(self.update_orb)
            self.kernel.start()
            self.active = True
            self.toggle_btn.text = "Stop"
            self.status.text = "Neuro-Sync Active"

    def update_orb(self, gcl: float, is_safe: bool):
        if is_safe:
            self.orb_color.rgb = (1.0 - gcl, gcl, 0.2)
            self.status.text = f"Coherence: {int(gcl * 100)}%"
        else:
            self.orb_color.rgb = (1.0, 0.0, 0.0)
            self.status.text = "Regulation Mode (Muted)"


if __name__ == "__main__":
    GoeckohUI().run()
