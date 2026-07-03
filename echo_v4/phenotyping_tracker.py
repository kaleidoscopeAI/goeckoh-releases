from enum import Enum
from typing import List, Optional
from dataclasses import dataclass
import numpy as np
import cv2  # Open-source for gesture (new: multimodal from findings)
import time

class FragmentClass(Enum):
    CLEAR_SPEECH = "clear_speech"
    AMBIGUOUS = "ambiguous"
    NONVERBAL = "nonverbal"
    GESTURE = "gesture"  # New: for nonverbal autistics

@dataclass
class FragmentMetadata:
    timestamp: float
    audio: np.ndarray
    vad_score: float
    asr_confidence: float
    triggered_by: str
    classification: FragmentClass
    gesture_detected: bool = False  # New

class PhenotypingTracker:
    def __init__(self):
        self.fragments: List[FragmentMetadata] = []

    def classify_fragment(self, audio: np.ndarray, vad_score: float, asr_confidence: float, trigger: str, frame: np.ndarray = None) -> FragmentClass:
        if asr_confidence > 0.85 and vad_score > 0.7: return FragmentClass.CLEAR_SPEECH
        elif vad_score > 0.3: return FragmentClass.AMBIGUOUS
        # New: Gesture detection (simple edge detect)
        if frame is not None and np.mean(cv2.Canny(frame, 100, 200)) > 50: return FragmentClass.GESTURE
        return FragmentClass.NONVERBAL

    def record_fragment(self, audio: np.ndarray, vad_score: float, asr_confidence: float, trigger: str, frame: np.ndarray = None) -> FragmentMetadata:
        label = self.classify_fragment(audio, vad_score, asr_confidence, trigger, frame)
        meta = FragmentMetadata(
            timestamp=time.time(), audio=audio, vad_score=vad_score, asr_confidence=asr_confidence,
            triggered_by=trigger, classification=label, gesture_detected=frame is not None
        )
        self.fragments.append(meta)
        return meta

    def summary_counts(self) -> dict:
        counts = {cls.value: sum(f.classification == cls for f in self.fragments) for cls in FragmentClass}
        counts["gestures"] = sum(f.gesture_detected for f in self.fragments)  # New
        return counts
