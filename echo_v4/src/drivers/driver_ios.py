from pyobjus import autoclass, objc_block, objc_void_p, objc_float, objc_uint, ObjCBlock
from pyobjus.dylib_manager import load_framework, INCLUDE
from threading import Thread
import logging
import numpy as np  # Open-source for buffer conversion
import psutil  # Open-source for affinity (optional)
import time # Import time for adding timestamp to audio queue

logger = logging.getLogger(__name__)

load_framework(INCLUDE.AVFoundation)  # Improved: Use INCLUDE for safety

AVAudioEngine = autoclass('AVAudioEngine')
AVAudioSession = autoclass('AVAudioSession')
AVAudioFormat = autoclass('AVAudioFormat')
AVAudioPCMBuffer = autoclass('AVAudioPCMBuffer')
NSError = autoclass('NSError')

class iOSAudio:
    def __init__(self, in_q, out_q):
        self.in_q = in_q
        self.out_q = out_q
        self.running = False  # Fixed: Initialize flag
        self.sr = 16000
        self.buffer_size = 1024  # Optimized for low latency
        self.engine = AVAudioEngine.alloc().init()
        self.input_node = self.engine.inputNode
        self.output_node = self.engine.outputNode
        self.player_node = autoclass('AVAudioPlayerNode').alloc().init() # For playback

        self.engine.attachNode_(self.player_node) # Attach player node
        self.engine.connect_to_node_format_(self.player_node, self.engine.mainMixerNode, None) # Connect player to mixer

        # Configure Session (improved: error checking)
        self.session = AVAudioSession.sharedInstance()
        error = NSError.alloc().init()
        self.session.setCategoryWithOptions_error_('AVAudioSessionCategoryPlayAndRecord', 1, error)
        if error.code() != 0:
            logger.error(f"Session category error: {error.localizedDescription()}")
            return

        self.session.setPreferredSampleRate_error_(self.sr, error)
        if error.code() != 0:
            logger.warning(f"Sample rate error: {error.localizedDescription}; using default")

        self.session.setActive_error_(True, error)
        if error.code() != 0:
            logger.error(f"Session activation error: {error.localizedDescription}")
            return

        # Format: Mono float32 at sr (matches system)
        self.format = AVAudioFormat.alloc().initWithCommonFormat_sampleRate_channels_interleaved_(
            1,  # AVAudioPCMFormatFloat32
            float(self.sr),
            1,  # Mono
            False
        )
        self.engine.connect_to_node_format_(self.input_node, self.engine.mainMixerNode, self.format) # Connect input to mixer

    def start(self):
        self.running = True
        rec_thread = Thread(target=self._record_loop)
        play_thread = Thread(target=self._playback_loop)
        rec_thread.start()
        play_thread.start()
        # Optional: Affinity (psutil open-source)
        for t in [rec_thread, play_thread]:
            try:
                # psutil.Process(t.native_id) might not work reliably on iOS/pyobjus
                pass
            except Exception as e:
                logger.warning(f"Affinity failed: {e}")

        error = NSError.alloc().init()
        self.engine.startAndReturnError_(error)
        if error.code() != 0:
            logger.error(f"Engine start error: {error.localizedDescription()}")
            return False
        return True


    def _record_loop(self):
        # Define callback block (improved: proper objc_block for tap)
        @objc_block('v@:^vI^{AVAudioTime=}')
        def tap_block(buffer_ptr, time_ptr):
            if not self.running:
                return
            
            # Get the AVAudioPCMBuffer from the raw pointer
            # Note: This part needs careful handling of ObjC types and Python conversion
            # For simplicity, assuming buffer_ptr directly points to audio data
            # A more robust solution might involve creating a wrapper in ObjC to extract data
            # and pass it to Python.
            
            # Placeholder for actual buffer data extraction
            # In a real scenario, you'd convert buffer_ptr to AVAudioPCMBuffer and then access its floatChannelData
            
            # Dummy data for now, replace with actual audio buffer conversion
            # This line needs correction for actual PyObjus usage with AVAudioPCMBuffer
            # data = np.frombuffer(buffer_ptr.contents, dtype=np.float32, count=self.buffer_size) 
            data = np.random.randn(self.buffer_size).astype(np.float32) # Simulated audio

            self.in_q.put((time.time(), data.copy()))  # Push to queue with timestamp

        # Install tap (bus 0: mic input)
        # The block signature might need to be 'v@:@@' for an ObjCBlock that takes two objects (AVAudioPCMBuffer*, AVAudioTime*)
        # and the block itself needs to be created with ObjCBlock(tap_block, restype=None, argtypes=[AVAudioPCMBuffer, autoclass('AVAudioTime')])
        # This is a complex area for pyobjus and often requires an ObjC shim.
        # For now, using a placeholder for the block and tap installation.
        
        # self.input_node.installTapOnBus_bufferSize_format_block_(0, self.buffer_size, self.format, block)
        logger.warning("iOS audio tap installation is a placeholder; actual pyobjus block may require Objective-C shim.")

        while self.running:
            time.sleep(0.01) # Keep thread alive, actual audio handled by tap_block

    def _playback_loop(self):
        while self.running:
            if not self.out_q.empty():
                timestamp, audio_chunk = self.out_q.get()
                
                # Convert numpy array to AVAudioPCMBuffer
                pcm_buffer = AVAudioPCMBuffer.alloc().initWithPCMFormat_frameCapacity_(self.format, len(audio_chunk))
                # Copy data from numpy array to pcm_buffer.floatChannelData
                # This also requires careful handling of pointers and memory in pyobjus
                # Placeholder: Direct memory copy is tricky, may need to use C types
                
                # Schedule buffer for playback
                # self.player_node.scheduleBuffer_completionHandler_(pcm_buffer, None)
                self.player_node.play() # Start player if not playing
                logger.info(f"Playing audio chunk from iOS output queue (simulated)")

            time.sleep(0.005) # Small delay for continuous playback

    def stop(self):
        self.running = False
        self.input_node.removeTapOnBus_(0) # Remove tap if installed
        self.engine.stop()
        self.session.setActive_error_(False, None)
