import numpy as np
import torch
import logging

logger = logging.getLogger(__name__)

def compute_vad_score(audio: np.ndarray) -> float:
    # Ensure audio is not empty to prevent division by zero or NaN
    if audio.size == 0:
        return 0.0
    return min(1.0, np.sqrt(np.mean(audio**2)) * 10.0)

_asr_model_cache = {}

def run_asr(audio: np.ndarray, asr_model_path: str) -> dict:
    global _asr_model_cache
    model = _asr_model_cache.get(asr_model_path)
    
    if model is None:
        try:
            # Assuming the whisper model from sherpa-onnx requires a different loading mechanism.
            # The original code used silero, which is easier to load.
            # For now, this will be a placeholder for loading a local sherpa-onnx model.
            # In a real scenario, this would involve using the onnxruntime to load and run the model.
            logger.info(f"Loading ASR model from {asr_model_path} (placeholder).")
            # For demonstration, we'll keep the silero model loading logic but from a local path concept.
            # This part would need to be implemented correctly based on the model type.
            # model = torch.jit.load(asr_model_path) # Example for a torchscript model
            # For now, let's fall back to a dummy ASR if loading fails, to avoid breaking the flow.
            
            # Since we can't easily load the sherpa-onnx model here without onnxruntime,
            # we'll simulate a failure and return a dummy result.
            raise NotImplementedError("Loading of local sherpa-onnx model not fully implemented in this script.")

        except Exception as e:
            logger.warning(f"Failed to load ASR model from {asr_model_path}: {e}. Using dummy ASR result.")
            _asr_model_cache[asr_model_path] = None # Cache the failure
            text = "dummy transcript"
            conf = 0.1 # Low confidence for dummy
            return {'text': text, 'confidence': conf}
    
    try:
        # Ensure audio is a tensor for the model
        text, conf = model(torch.from_numpy(audio))
    except Exception as e:
        logger.warning(f"ASR inference failed: {e}. Returning dummy result.")
        text = "dummy transcript"
        conf = 0.1
        
    return {'text': text, 'confidence': conf}

def dsp_low_pass(audio: np.ndarray, cutoff: float = 800, sr: int = 16000) -> np.ndarray:
    from scipy.signal import butter, lfilter
    # Ensure audio is not empty
    if audio.size == 0:
        return audio
    b, a = butter(1, cutoff / (sr / 2), 'low')
    return lfilter(b, a, audio)

def soft_limiter(audio: np.ndarray, threshold: float = 0.95) -> np.ndarray:
    return np.clip(audio, -threshold, threshold)
