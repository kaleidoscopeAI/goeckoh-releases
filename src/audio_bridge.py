import threading
import time
import numpy as np


class AudioBridge:
    """
    Pulls mic frames from AndroidAudioIO.in_rb, performs VAD/ASR/Mirror/TTS off the audio threads,
    and pushes speaker frames into AndroidAudioIO.out_rb.

    Heavy work happens on this worker thread, never in the capture/play callbacks.

    Plug-ins:
      - vad (optional): callable(frame, sr)->bool
      - harvester: SmartHarvester
      - asr: object with transcribe(audio, sr)->str
      - mirror: FastMirror
      - tts: object with synthesize(text, sr) or synthesize_stream(...)
      - heart: object with get_gcl()->float (for gating)
    """

    def __init__(
        self,
        audio_io,
        sr=16000,
        frame_size=320,
        vad=None,
        harvester=None,
        asr=None,
        mirror=None,
        tts=None,
        heart=None,
    ):
        self.audio = audio_io
        self.sr = int(sr)
        self.frame_size = int(frame_size)

        self.vad = vad
        self.harvester = harvester
        self.asr = asr
        self.mirror = mirror
        self.tts = tts
        self.heart = heart

        self._running = False
        self._t = None

        # buffering utterances
        self._utt = []
        self._speech_frames = 0
        self._silence_frames = 0

        # tuning
        self.min_utt_frames = int(0.35 * self.sr / self.frame_size)  # ~350ms
        self.end_silence_frames = int(0.25 * self.sr / self.frame_size)  # ~250ms

    def start(self):
        if self._running:
            return
        self._running = True
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            frame = self.audio.in_rb.pop()
            if frame is None:
                time.sleep(0.002)
                continue

            is_speech = True
            if self.vad is not None:
                try:
                    is_speech = bool(self.vad(frame, self.sr))
                except Exception:
                    is_speech = True

            # Always feed harvester (it has its own gates)
            if self.harvester is not None:
                try:
                    self.harvester.submit_fragment(frame, sr=self.sr)
                except Exception:
                    pass

            # Simple utterance segmentation using VAD
            if is_speech:
                self._utt.append(frame)
                self._speech_frames += 1
                self._silence_frames = 0
            else:
                if self._utt:
                    self._silence_frames += 1

                # finalize utterance
                if self._utt and self._silence_frames >= self.end_silence_frames:
                    if self._speech_frames >= self.min_utt_frames:
                        audio_utt = np.concatenate(self._utt, axis=0)
                        self._handle_utterance(audio_utt)
                    # reset
                    self._utt = []
                    self._speech_frames = 0
                    self._silence_frames = 0

    def _handle_utterance(self, audio_utt: np.ndarray):
        # 1) ASR
        text = ""
        if self.asr is not None:
            try:
                text = self.asr.transcribe(audio_utt, self.sr)
            except Exception:
                text = ""
        if not text:
            return

        # 2) GCL gating
        gcl = 1.0
        if self.heart is not None and hasattr(self.heart, "get_gcl"):
            try:
                gcl = float(self.heart.get_gcl())
            except Exception:
                gcl = 1.0

        # 3) Mirror
        corrected = text
        if self.mirror is not None:
            try:
                corrected = self.mirror.reflect(text, gcl=gcl)
            except Exception:
                corrected = text

        if not corrected:
            return

        # 4) TTS
        if self.tts is None:
            out = self._beep(0.12, 440.0)
            self._push_audio(out)
            return

        if hasattr(self.tts, "synthesize_stream"):
            try:
                for chunk in self.tts.synthesize_stream(corrected, sr=self.sr, chunk_frames=self.frame_size):
                    self._push_audio(chunk)
                return
            except Exception:
                pass

        try:
            out = self.tts.synthesize(corrected, sr=self.sr)
        except Exception:
            out = self._beep(0.12, 440.0)

        self._push_audio(out)

    def _push_audio(self, audio: np.ndarray):
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        n = len(audio)
        i = 0
        while i < n:
            chunk = audio[i : i + self.frame_size]
            if len(chunk) < self.frame_size:
                pad = np.zeros(self.frame_size, dtype=np.float32)
                pad[: len(chunk)] = chunk
                chunk = pad

            ok = self.audio.out_rb.push(chunk)
            if not ok:
                break  # drop-not-block
            i += self.frame_size

    def _beep(self, seconds=0.1, hz=440.0):
        t = np.linspace(0, seconds, int(self.sr * seconds), endpoint=False)
        x = 0.12 * np.sin(2 * np.pi * hz * t).astype(np.float32)
        return x
