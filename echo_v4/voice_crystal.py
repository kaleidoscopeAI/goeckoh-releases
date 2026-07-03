import numpy as np
import torch
from utils import soft_limiter
import logging

logger = logging.getLogger(__name__)

class VoiceCrystal:
    def __init__(self, vad_model_path: str, tts_model_path: str):
        self.embedding_history = []
        self.current_embedding = None
        self.alpha = 0.01  # Slow drift (AIM)
        self.vad_model_path = vad_model_path
        self.tts_model_path = tts_model_path
        
        # Load models on initialization
        try:
            self.vad_model = torch.jit.load(self.vad_model_path)
        except Exception as e:
            logger.error(f"Failed to load VAD model from {self.vad_model_path}: {e}")
            self.vad_model = None

        try:
            # This assumes piper is a jit model, which might not be the case.
            # The original code used torch.hub.load('rhasspy/piper', 'en_US')
            # For now, we'll assume a local path can be used. This may need adjustment
            # based on how piper models are actually packaged.
            self.tts_model = torch.jit.load(self.tts_model_path)
        except Exception as e:
            logger.error(f"Failed to load TTS model from {self.tts_model_path}: {e}")
            self.tts_model = None

    def update_with_fragment(self, audio_fragment: np.ndarray):
        # Extract embedding (Torch-based, offline XTTS-like)
        if not self.vad_model:
            logger.warning("VAD model not loaded, using dummy embedding.")
            embedding = torch.randn(1, 256)
        else:
            with torch.no_grad():
                try:
                    # The silero_vad model expects a 1D tensor
                    audio_tensor = torch.from_numpy(audio_fragment.astype(np.float32))
                    embedding = self.vad_model(audio_tensor)
                except Exception as e:
                    logger.warning(f"Silero VAD embedding failed: {e}. Using dummy embedding.")
                    embedding = torch.randn(1, 256) # Dummy embedding

        if self.current_embedding is None:
            self.current_embedding = embedding
        else:
            self.current_embedding = (1 - self.alpha) * self.current_embedding + self.alpha * embedding
        self.embedding_history.append(embedding)

        # Dysarthric adapt: Add noise for realism in nonverbal (new)
        if len(audio_fragment) < 1000:  # Short fragment
            audio_fragment += np.random.normal(0, 0.01, len(audio_fragment))

    def synthesize(self, text: str) -> np.ndarray:
        # Offline TTS (Piper-like via Torch)
        if not self.tts_model:
            logger.warning("TTS model not loaded, using dummy audio.")
            return np.random.randn(16000)

        try:
            # This is a placeholder for actual synthesis logic with a local piper model
            # The original torch.hub call abstracts this away. A real implementation
            # would require knowing how to invoke the local piper model files.
            logger.info("Synthesizing with local TTS model (placeholder).")
            # For now, return dummy audio.
            audio = np.random.randn(16000) # Dummy audio
        except Exception as e:
            logger.warning(f"Piper TTS synthesis failed: {e}. Using dummy audio.")
            audio = np.random.randn(16000) # Dummy audio
        return soft_limiter(audio)

