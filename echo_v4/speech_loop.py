import numpy as np
import threading
import queue
import time
import logging
from typing import Dict, Any, Optional
import json

from phenotyping_tracker import FragmentClass, FragmentMetadata, PhenotypingTracker
from voice_crystal import VoiceCrystal
from utils import compute_vad_score, run_asr, dsp_low_pass, soft_limiter
from system_state import SystemState # Import SystemState
from crystalline_heart import MobileCrystallineHeart # Import MobileCrystallineHeart

logger = logging.getLogger(__name__)

class SpeechLoop:
    """Main speech processing loop with Crystalline Heart integration"""
    
    def __init__(self, 
                 system_state: SystemState,
                 crystalline_heart: MobileCrystallineHeart,
                 phenotyping_tracker: PhenotypingTracker, # Added phenotyping_tracker
                 voice_crystal: VoiceCrystal, # Added voice_crystal
                 audio_input_queue: queue.Queue, # Pass input queue directly
                 audio_output_queue: queue.Queue,
                 asr_model_path: str): # Pass ASR model path
        
        self.system_state = system_state
        self.heart = crystalline_heart
        self.tracker = phenotyping_tracker # Renamed from tracker to phenotyping_tracker for clarity
        self.voice_crystal = voice_crystal # Now initialized here
        self.asr_model_path = asr_model_path

        # Speech processing parameters
        self.vad_threshold = 0.3
        self.min_utterance_length = 0.1  # seconds
        self.max_utterance_length = 5.0   # seconds
        
        # State management
        self.current_utterance = []
        self.utterance_start_time = 0
        self.is_speaking = False
        
        # Processing queues
        self.audio_input_queue = audio_input_queue # Direct assignment
        self.audio_output_queue = audio_output_queue # Direct assignment
        
        # Voice Crystal integration (already passed in init)
        self.prosody_model = None # Placeholder
        
        # Start processing thread
        self.running = False
        self.processing_thread = threading.Thread(target=self._processing_loop)
    
    def start(self):
        """Start the speech loop"""
        self.running = True
        self.processing_thread.start()
        logger.info("Speech Loop started")
    
    def stop(self):
        """Stop the speech loop"""
        self.running = False
        if self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        logger.info("Speech Loop stopped")
    
    def _processing_loop(self):
        """Main processing loop - runs in separate thread"""
        frame_count = 0
        last_heart_update = time.time()
        
        while self.running:
            try:
                # Get audio frame (non-blocking)
                timestamp, audio_frame = None, None
                try:
                    timestamp, audio_frame = self.audio_input_queue.get(timeout=0.001)
                    frame_count += 1
                except queue.Empty:
                    # No audio, update heart with minimal input
                    if time.time() - last_heart_update > 0.1:  # 10Hz update
                        self._update_heart_with_background()
                        last_heart_update = time.time()
                    time.sleep(0.001) # Small sleep to prevent busy waiting
                    continue
                
                # Process frame start time
                process_start = time.time()
                
                # 1. Extract audio features
                features = self._extract_audio_features(audio_frame)
                
                # 2. Voice Activity Detection
                is_speech = self._vad_detection(features)
                
                # 3. Update utterance buffer
                self._update_utterance_buffer(audio_frame, is_speech, timestamp)
                
                # 4. If utterance is complete, process it
                if not self.is_speaking and len(self.current_utterance) > 0:
                    self._process_complete_utterance()
                
                # 5. Update Crystalline Heart with audio features
                heart_input = self._create_heart_input(features, is_speech)
                heart_result = self.heart.update(heart_input, dt=0.01)
                
                # 6. Update system state
                self.system_state.update_from_crystalline_heart(
                    heart_result["gcl"], 
                    heart_result["energy"]
                )
                
                # 7. Adjust processing based on GCL
                self._adjust_processing_by_gcl()
                
                # Calculate and update latency
                processing_time = (time.time() - process_start) * 1000
                audio_latency = (process_start - timestamp) * 1000 if timestamp else 0
                
                self.system_state.processing_latency_ms = processing_time
                self.system_state.audio_latency_ms = audio_latency
                
                # Update timestamp
                last_heart_update = time.time()
                
                # Every 100 frames, log performance
                if frame_count % 100 == 0:
                    self._log_performance_metrics()
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                time.sleep(0.01)  # Prevent tight loop on error
    
    def _extract_audio_features(self, audio_frame: np.ndarray) -> Dict[str, float]:
        """Extract features for VAD and heart input"""
        # Basic features (could be extended with MFCC, etc.)
        rms = np.sqrt(np.mean(audio_frame ** 2))
        
        # Avoid division by zero for silent frames
        if np.sum(np.abs(audio_frame)) == 0:
            zero_crossing_rate = 0.0
        else:
            zero_crossing_rate = np.mean(np.abs(np.diff(np.sign(audio_frame)))) / 2
        
        # Spectral features (simplified)
        if len(audio_frame) > 0:
            fft_output = np.fft.rfft(audio_frame)
            frequencies = np.fft.rfftfreq(len(audio_frame), 1/self.system_state.sr if hasattr(self.system_state, 'sr') else 16000) # Assuming sr is in system_state or default
            
            # Avoid division by zero
            sum_abs_fft = np.sum(np.abs(fft_output))
            if sum_abs_fft > 0:
                spectral_centroid = np.sum(np.abs(fft_output) * frequencies) / sum_abs_fft
            else:
                spectral_centroid = 0.0

            # spectral_flatness
            # Add a small constant to avoid log(0)
            if np.all(np.abs(fft_output) == 0):
                spectral_flatness = 0.0
            else:
                geometric_mean = np.exp(np.mean(np.log(np.abs(fft_output) + 1e-10)))
                arithmetic_mean = np.mean(np.abs(fft_output))
                spectral_flatness = geometric_mean / arithmetic_mean if arithmetic_mean > 0 else 0.0
        else:
            spectral_centroid = 0.0
            spectral_flatness = 0.0
        
        return {
            "rms": float(rms),
            "zcr": float(zero_crossing_rate),
            "spectral_centroid": float(spectral_centroid),
            "spectral_flatness": float(spectral_flatness),
            "timestamp": time.time()
        }
    
    def _vad_detection(self, features: Dict[str, float]) -> bool:
        """Voice Activity Detection adjusted by GCL"""
        base_threshold = self.vad_threshold
        
        # Adjust sensitivity based on GCL
        if self.system_state.gcl < 0.5:
            # Lower sensitivity in crisis to reduce false positives
            adjusted_threshold = base_threshold * 1.5
        elif self.system_state.gcl > 0.8:
            # Higher sensitivity in flow state
            adjusted_threshold = base_threshold * 0.8
        else:
            adjusted_threshold = base_threshold
        
        # Simple energy-based VAD
        is_speech = features["rms"] > adjusted_threshold
        
        # Additional checks for stability
        if features["zcr"] > 0.5:  # Likely noise
            is_speech = False
        
        return is_speech
    
    def _update_utterance_buffer(self, 
                                audio_frame: np.ndarray, 
                                is_speech: bool, 
                                timestamp: float):
        """Manage the current utterance buffer"""
        current_time = time.time()
        
        if is_speech:
            if not self.is_speaking:
                # Start new utterance
                self.is_speaking = True
                self.utterance_start_time = timestamp
                self.current_utterance = [audio_frame]
                logger.debug(f"Utterance started at {timestamp}")
            else:
                # Continue utterance
                self.current_utterance.append(audio_frame)
                
                # Check if utterance is too long
                utterance_duration = current_time - self.utterance_start_time
                if utterance_duration > self.max_utterance_length:
                    logger.warning(f"Utterance too long ({utterance_duration:.1f}s), forcing end")
                    self._process_complete_utterance()
        else:
            if self.is_speaking:
                # End of utterance
                utterance_duration = current_time - self.utterance_start_time
                
                if utterance_duration >= self.min_utterance_length:
                    # Valid utterance, process it
                    self._process_complete_utterance()
                else:
                    # Too short, discard
                    logger.debug(f"Utterance too short ({utterance_duration:.1f}s), discarded")
                    self.current_utterance = []
                    self.is_speaking = False
    
    def _process_complete_utterance(self):
        """Process a complete utterance"""
        if not self.current_utterance or len(self.current_utterance) == 0:
            return
        
        try:
            # Concatenate audio frames
            full_utterance = np.concatenate(self.current_utterance)

            # Perform ASR
            asr_result = run_asr(full_utterance, asr_model_path=self.asr_model_path)
            transcript = asr_result.get("text", "")
            asr_confidence = asr_result.get("confidence", 0.0)

            # Record the fragment with full context
            vad_score = compute_vad_score(full_utterance)
            trigger_source = "ASR" if asr_confidence > 0.7 else "AMBIGUOUS_VOICE"
            fragment_meta = self.tracker.record_fragment(full_utterance, vad_score, asr_confidence, trigger_source)

            # Update VoiceCrystal
            if fragment_meta.classification != FragmentClass.NONVERBAL:
                filtered_audio = dsp_low_pass(full_utterance, cutoff=800)
                self.voice_crystal.update_with_fragment(filtered_audio)
            
            # Apply GCL-based processing
            if self.system_state.gcl < 0.3:
                # Crisis mode - minimal processing
                response_audio = self._crisis_mode_response(full_utterance)
            elif self.system_state.gcl < 0.7:
                # Standard processing
                response_audio = self._standard_processing(full_utterance, transcript)
            else:
                # Flow state - enhanced processing
                response_audio = self._enhanced_processing(full_utterance, transcript)
            
            # Send response to audio output
            if response_audio is not None and self.audio_output_queue:
                self.audio_output_queue.put((time.time(), response_audio))
                logger.info(f"Processed utterance: '{transcript}', GCL={self.system_state.gcl:.2f}")
            
        except Exception as e:
            logger.error(f"Error processing utterance: {e}")
        
        finally:
            # Reset utterance state
            self.current_utterance = []
            self.is_speaking = False
    
    def _crisis_mode_response(self, utterance: np.ndarray) -> Optional[np.ndarray]:
        """Minimal response in crisis mode"""
        # Simple calming affirmation
        # In production, this would use TTS
        logger.info("Crisis mode: Sending calming response")
        
        # For now, return a simple tone
        duration = 0.5
        t = np.linspace(0, duration, int(16000 * duration), False)
        tone = 0.1 * np.sin(2 * np.pi * 440 * t).astype(np.float32)  # A4 note
        
        return tone
    
    def _standard_processing(self, utterance: np.ndarray) -> Optional[np.ndarray]:
        """Standard speech processing"""
        # Placeholder for actual ASR + TTS pipeline
        # This would integrate with your Voice Crystal
        
        logger.info("Standard processing of utterance")
        
        # Echo back with slight modification (simulating correction)
        # In production, this would be the Voice Crystal output
        return (utterance * 0.8).astype(np.float32)  # Simple attenuation for demo
    
    def _enhanced_processing(self, utterance: np.ndarray) -> Optional[np.ndarray]:
        """Enhanced processing in flow state"""
        logger.info("Enhanced processing with prosody modeling")
        
        # More sophisticated processing
        # Could include emotion recognition, complex corrections, etc.
        
        return utterance.astype(np.float32)  # Placeholder
    
    def _create_heart_input(self, 
                           features: Dict[str, float], 
                           is_speech: bool) -> np.ndarray:
        """Create input vector for Crystalline Heart"""
        # Map audio features to heart input dimensions
        input_vector = np.zeros(self.heart.n_nodes)
        
        # First node: speech activity
        input_vector[0] = 1.0 if is_speech else 0.0
        
        # Second node: audio energy
        input_vector[1] = features["rms"]
        
        # Third node: spectral complexity
        input_vector[2] = features["spectral_centroid"] / 1000
        
        # Fourth node: noise-like quality
        input_vector[3] = features["zcr"]
        
        # Remaining nodes: random but correlated with speech state
        if is_speech:
            input_vector[4:] = np.random.randn(self.heart.n_nodes - 4) * 0.1 + 0.2
        else:
            input_vector[4:] = np.random.randn(self.heart.n_nodes - 4) * 0.05
        
        return input_vector
    
    def _update_heart_with_background(self):
        """Update heart with minimal background input"""
        background_input = np.random.randn(self.heart.n_nodes) * 0.01
        self.heart.update(background_input, dt=0.1)
    
    def _adjust_processing_by_gcl(self):
        """Adjust processing parameters based on GCL"""
        # Adjust VAD threshold
        if self.system_state.gcl < 0.5:
            self.vad_threshold *= 1.1  # Less sensitive
        elif self.system_state.gcl > 0.8:
            self.vad_threshold *= 0.9  # More sensitive
        
        # Clamp threshold
        self.vad_threshold = max(0.1, min(0.5, self.vad_threshold))
        
        # Adjust utterance length limits
        if self.system_state.gcl < 0.3:
            self.max_utterance_length = 2.0  # Shutter in crisis
        else:
            self.max_utterance_length = 5.0
    
    def _log_performance_metrics(self):
        """Log performance metrics periodically"""
        metrics = {
            "gcl": self.system_state.gcl,
            "stability_band": self.system_state.stability_band,
            "audio_latency_ms": self.system_state.audio_latency_ms,
            "processing_latency_ms": self.system_state.processing_latency_ms,
            "vad_threshold": self.vad_threshold,
            "input_queue_size": self.audio_input_queue.qsize(),
            "output_queue_size": self.audio_output_queue.qsize(),
            "timestamp": time.time()
        }
        
        logger.info(f"SpeechLoop Performance: {json.dumps(metrics, indent=None)}")