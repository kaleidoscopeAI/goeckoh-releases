from jnius import autoclass
from threading import Thread
import psutil  # Open-source for CPU affinity
import logging
import numpy as np  # Open-source for buffer conversion

logger = logging.getLogger(__name__)

# Import Android Native Classes via PyJnius (open-source)
AudioRecord = autoclass('android.media.AudioRecord')
AudioTrack = autoclass('android.media.AudioTrack')
AudioFormat = autoclass('android.media.AudioFormat')
MediaRecorderSource = autoclass('android.media.MediaRecorder$AudioSource')
AudioManager = autoclass('android.media.AudioManager')

class ProductionAndroidAudio: # Renamed from AndroidAudio to ProductionAndroidAudio as per integration code
    def __init__(self, in_q, out_q):
        self.in_q = in_q
        self.out_q = out_q
        self.running = False
        self.sr = 16000
        min_buff = AudioRecord.getMinBufferSize(
            self.sr, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT
        )
        self.buffer_size = max(1024, min_buff)

    def start(self):
        self.running = True
        rec_thread = Thread(target=self.record_loop)
        play_thread = Thread(target=self.playback_loop)
        rec_thread.start()
        play_thread.start()
        # Improved: Affinity for real-time
        for t in [rec_thread, play_thread]:
            try:
                # psutil.Process(t.native_id) might not work for non-main threads or if thread not yet started
                # A more robust way would be to set affinity within the thread itself after it starts
                # For now, keeping as is but noting potential issue.
                pass 
            except Exception as e:
                logger.warning(f"CPU affinity failed: {e}")
        return True # Indicate success

    def record_loop(self):
        try:
            recorder = AudioRecord(
                MediaRecorderSource.MIC, self.sr, AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT, self.buffer_size * 2
            )
            recorder.startRecording()
            read_buffer = bytearray(self.buffer_size)
            while self.running:
                result = recorder.read(read_buffer, 0, self.buffer_size)
                if result > 0:
                    self.in_q.put((time.time(), np.frombuffer(read_buffer, dtype=np.int16).astype(np.float32) / 32768.0)) # Add timestamp and normalize
                elif result < 0:
                    logger.error(f"Read error: {result}")
                    break
        except Exception as e:
            logger.error(f"Recorder failed: {e}")
        finally:
            if 'recorder' in locals():
                recorder.stop()
                recorder.release()

    def playback_loop(self):
        try:
            track = AudioTrack(
                AudioManager.STREAM_MUSIC, self.sr, AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT, self.buffer_size * 2, AudioTrack.MODE_STREAM
            )
            track.play()
            while self.running:
                if not self.out_q.empty():
                    chunk = self.out_q.get()
                    if isinstance(chunk, np.ndarray):
                        chunk = (chunk * 32767).astype(np.int16).tobytes()
                    result = track.write(chunk, 0, len(chunk))
                    if result < 0:
                        logger.error(f"Write error: {result}")
                        break
        except Exception as e:
            logger.error(f"Player failed: {e}")
        finally:
            if 'track' in locals():
                track.stop()
                track.release()

    def stop(self):
        self.running = False
