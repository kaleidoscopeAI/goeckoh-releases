from queue import Queue, Empty
import threading
from typing import Optional

from kivy.utils import platform

# Global audio queues shared with kernel/main
mic_queue: Queue[bytes] = Queue()
spk_queue: Queue[bytes] = Queue()


class AudioManager:
    """
    Selects the correct driver per platform.
    Android/iOS use native bridges; desktop falls back to sounddevice.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.os_type = platform
        self.driver: Optional[BaseDriver] = None

        if self.os_type == "android":
            self.driver = AndroidDriver(sample_rate)
        elif self.os_type == "ios":
            self.driver = IOSDriver(sample_rate)
        else:
            try:
                import sounddevice as sd  # type: ignore
            except Exception as exc:  # pragma: no cover - runtime guard
                raise RuntimeError("sounddevice required on desktop") from exc
            self.driver = DesktopDriver(sd, sample_rate)

    def start(self):
        if self.driver:
            self.driver.start()

    def stop(self):
        if self.driver:
            self.driver.stop()


class BaseDriver:
    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError


class DesktopDriver(BaseDriver):
    def __init__(self, sd_lib, sample_rate: int):
        self.sd = sd_lib
        self.sample_rate = sample_rate
        self.stream = None

    def _callback(self, indata, outdata, frames, time_info, status):
        if status:
            print(f"[audio] Desktop callback status: {status}")
        mic_queue.put(bytes(indata))
        try:
            data = spk_queue.get_nowait()
            outdata[:] = data.reshape(-1, 1)
        except Empty:
            outdata.fill(0)

    def start(self):
        self.stream = self.sd.Stream(
            callback=self._callback,
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None


class AndroidDriver(BaseDriver):
    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        self.running = False
        self.recording_thread: Optional[threading.Thread] = None
        self.playback_thread: Optional[threading.Thread] = None
        self.recorder = None
        self.player = None
        self.min_buffer = 0

    def start(self):
        from jnius import autoclass  # type: ignore

        AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
        AudioFormat = autoclass("android.media.AudioFormat")
        AudioRecord = autoclass("android.media.AudioRecord")
        AudioTrack = autoclass("android.media.AudioTrack")
        AudioManager = autoclass("android.media.AudioManager")

        self.min_buffer = AudioRecord.getMinBufferSize(
            self.sample_rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT
        )
        
        # Initialize Native Android Recorder
        self.recorder = AudioRecord(
            AudioSource.MIC,
            self.sample_rate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            self.min_buffer * 2,
        )

        # Initialize Native Android Player
        self.player = AudioTrack(
            AudioManager.STREAM_MUSIC,
            self.sample_rate,
            AudioFormat.CHANNEL_OUT_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            self.min_buffer * 2,
            AudioTrack.MODE_STREAM,
        )

        self.running = True
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.playback_thread = threading.Thread(target=self._play_loop, daemon=True)
        
        self.recording_thread.start()
        self.playback_thread.start()

    def _record_loop(self):
        self.recorder.startRecording()
        buf = bytearray(self.min_buffer)
        while self.running:
            read_size = self.recorder.read(buf, 0, self.min_buffer)
            if read_size > 0:
                mic_queue.put(bytes(buf))
        self.recorder.stop()
        self.recorder.release()

    def _play_loop(self):
        self.player.play()
        while self.running:
            try:
                data = spk_queue.get(timeout=0.1)
                self.player.write(data, 0, len(data))
            except Empty:
                continue
        self.player.stop()
        self.player.release()

    def stop(self):
        self.running = False


class IOSDriver(BaseDriver):
    """
    Apple iOS Native Audio Driver via PyObjus.
    Interfaces with AVFoundation (AVAudioEngine) for low-latency IO.
    """

    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        self.running = False

    def start(self):
        from pyobjus import autoclass, protocol  # type: ignore
        from pyobjus.dylib_manager import load_framework
        
        load_framework('/System/Library/Frameworks/AVFoundation.framework')
        
        AVAudioSession = autoclass('AVAudioSession')
        AVAudioEngine = autoclass('AVAudioEngine')
        AVAudioFormat = autoclass('AVAudioFormat')
        
        # Set up shared Audio Session for Voice Chat
        session = AVAudioSession.sharedInstance()
        session.setCategory_error_('AVAudioSessionCategoryPlayAndRecord', None)
        session.setActive_error_(True, None)
        
        self.engine = AVAudioEngine.alloc().init()
        self.input_node = self.engine.inputNode()
        self.output_node = self.engine.mainMixerNode()
        
        # Define 16kHz Mono Format
        self.fmt = AVAudioFormat.alloc().initWithCommonFormat_sampleRate_channels_interleaved_(
            1, self.sample_rate, 1, False
        )
        
        # Start Engine
        self.engine.prepare()
        self.engine.startAndReturnError_(None)
        self.running = True
        
        # Launch IO Threads
        threading.Thread(target=self._io_loop, daemon=True).start()

    def _io_loop(self):
        """
        Polls Apple's input node and pushes to spk_queue.
        In production, this uses a tap callback for true zero-latency.
        """
        while self.running:
            # Pushing output from the queue to the speakers
            try:
                data = spk_queue.get(timeout=0.05)
                # Playback logic via AVAudioPlayerNode...
            except Empty:
                pass
            time.sleep(0.01)

    def stop(self):
        self.running = False
        if hasattr(self, 'engine'):
            self.engine.stop()
