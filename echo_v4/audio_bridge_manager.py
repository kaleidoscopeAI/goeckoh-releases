import queue
import time
import logging
import threading
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

class AudioBridgeManager:
    """Manages audio input/output between drivers and Speech Loop"""
    
    def __init__(self, platform: str = "android"):
        self.platform = platform
        self.audio_driver = None
        self.speech_loop = None
        
        # Audio buffers
        self.input_buffer = queue.Queue(maxsize=200)
        self.output_buffer = queue.Queue(maxsize=100)
        
        # Performance monitoring
        self.samples_processed = 0
        self.start_time = time.time()
        self.running = False
        self.bridge_thread = None
    
    def initialize(self):
        """Initialize platform-specific audio driver"""
        if self.platform == "android":
            from src.drivers.driver_android import ProductionAndroidAudio
            self.audio_driver = ProductionAndroidAudio(
                in_q=self.input_buffer,
                out_q=self.output_buffer
            )
        elif self.platform == "ios":
            from src.drivers.driver_ios import iOSAudio
            self.audio_driver = iOSAudio(
                in_q=self.input_buffer,
                out_q=self.output_buffer
            )
        else:
            logger.error(f"Platform '{self.platform}' is not supported for production audio. Exiting.")
            return False # Indicate failure
        
        logger.info(f"Audio driver initialized for {self.platform}")
        return True
    
    def connect_speech_loop(self, speech_loop):
        """Connect Speech Loop to audio bridge"""
        self.speech_loop = speech_loop
        # The speech_loop expects to get its audio from the input_buffer.
        # It also needs to put processed audio into the output_buffer for playback.
        self.speech_loop.audio_input_queue = self.input_buffer # Custom attribute for SpeechLoop
        self.speech_loop.audio_output_queue = self.output_buffer # Custom attribute for SpeechLoop
        
        # Start bridge thread
        self.running = True
        self.bridge_thread = threading.Thread(target=self._bridge_loop)
        self.bridge_thread.start()
        
        logger.info("Speech Loop connected to audio bridge")
    
    def _bridge_loop(self):
        """Bridge audio between driver and speech loop"""
        while self.running and self.speech_loop:
            try:
                # Monitor buffer levels
                input_level = self.input_buffer.qsize()
                output_level = self.output_buffer.qsize()
                
                # Adjust if buffers are getting too full
                if input_level > 150:
                    logger.warning(f"Input buffer overload: {input_level}")
                    # Drop some frames to recover
                    for _ in range(50):
                        try:
                            self.input_buffer.get_nowait()
                        except queue.Empty:
                            break
                
                # Log performance every 5 seconds
                if time.time() - self.start_time > 5:
                    # Assuming an average chunk size for calculation
                    avg_chunk_size = 1024 # Placeholder
                    sample_rate = self.samples_processed * avg_chunk_size / (time.time() - self.start_time)
                    logger.info(f"Audio bridge: {sample_rate:.0f} samples/sec")
                    self.samples_processed = 0
                    self.start_time = time.time()
                
                time.sleep(0.01)  # Prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Error in bridge loop: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start audio system"""
        if self.audio_driver:
            success = self.audio_driver.start()
            if success and self.speech_loop:
                # Speech loop's start method should handle its own processing thread
                pass # SpeechLoop will be started by EchoV4Application
            return success
        return False
    
    def stop(self):
        """Stop audio system"""
        self.running = False
        
        if self.speech_loop:
            self.speech_loop.stop()
        
        if self.audio_driver:
            self.audio_driver.stop()
        
        if self.bridge_thread and self.bridge_thread.is_alive():
            self.bridge_thread.join(timeout=1.0)
        
        logger.info("Audio bridge stopped")
    
    def _create_simulation_driver(self):
        """Create simulation driver for testing"""
        class SimulationAudio:
            def __init__(self, in_q, out_q):
                self.in_q = in_q
                self.out_q = out_q
                self.running = False
            
            def start(self):
                self.running = True
                # Generate test audio
                threading.Thread(target=self._generate_test_audio).start()
                threading.Thread(target=self._simulate_playback).start()
                return True
            
            def _generate_test_audio(self):
                """Generate simulated audio for testing"""
                sample_rate = 16000
                chunk_size = 1024
                
                while self.running:
                    # Generate tone that changes with time
                    t = np.linspace(0, chunk_size/sample_rate, chunk_size, False)
                    frequency = 440 + 100 * np.sin(time.time() * 0.5)
                    audio = 0.3 * np.sin(2 * np.pi * frequency * t)
                    
                    # Add some silence periodically
                    if int(time.time()) % 5 < 4:  # 4 seconds tone, 1 second silence
                        self.in_q.put((time.time(), audio.astype(np.float32))) # Add timestamp and ensure float32
                    
                    time.sleep(chunk_size / sample_rate)
            
            def _simulate_playback(self):
                """Simulate playback from output queue"""
                while self.running:
                    if not self.out_q.empty():
                        timestamp, chunk = self.out_q.get()
                        # Simulate playing audio
                        # logger.info(f"Simulating playback of audio chunk from {timestamp:.2f}")
                    time.sleep(0.005) # simulate playback rate

            def stop(self):
                self.running = False
        
        return SimulationAudio(self.input_buffer, self.output_buffer)
