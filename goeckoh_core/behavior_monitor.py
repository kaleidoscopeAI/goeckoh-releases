"""
GOECKOH - Behavior Monitor
Detects emotional states and dysregulation events from speech

This module analyzes:
1. Vocal prosody (pitch, energy, rate)
2. Speech patterns
3. Silence duration
4. Arousal and valence scoring
"""

import numpy as np
import librosa
from typing import Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class EmotionalState(Enum):
    """Emotional states the system can detect"""
    CALM = "calm"
    ANXIOUS = "anxious"
    HIGH_ENERGY = "high_energy"
    SHUTDOWN = "shutdown"
    PROGRESS = "progress"  # Successful self-regulation
    UNKNOWN = "unknown"

@dataclass
class BehaviorEvent:
    """Represents a detected behavioral/emotional event"""
    state: EmotionalState
    arousal: float  # 0-1 (low to high activation)
    valence: float  # -1 to +1 (negative to positive affect)
    confidence: float  # 0-1 (detection confidence)
    timestamp: datetime
    triggers: List[str]  # What caused this state
    
class BehaviorMonitor:
    """
    The Behavior Monitor continuously analyzes speech to detect
    emotional states and dysregulation events.
    
    Key Innovation: Multi-modal detection
    - Prosody (how they speak)
    - Content (what they say)
    - Timing (pauses, rate)
    - Pattern changes (deviation from baseline)
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.baseline_prosody = None
        self.event_history: List[BehaviorEvent] = []
        self.current_state = EmotionalState.CALM
        
        # Detection thresholds (tuned for autism/TBI/Alzheimer's)
        self.thresholds = {
            'high_pitch_variance': 50,  # Hz std deviation
            'fast_speech_rate': 200,  # words per minute
            'slow_speech_rate': 60,
            'long_pause': 3.0,  # seconds
            'high_energy': 0.15,  # RMS threshold
            'low_energy': 0.02
        }
        
        # Anxiety keywords (expandable)
        self.anxiety_keywords = [
            'scared', 'worried', 'nervous', 'afraid', 'help',
            'can\'t', 'won\'t', 'no', 'stop'
        ]
        
        # Progress keywords
        self.progress_keywords = [
            'good', 'happy', 'yes', 'okay', 'ready', 'better'
        ]
    
    def analyze(
        self,
        audio: np.ndarray,
        sample_rate: int,
        transcript: str = ""
    ) -> BehaviorEvent:
        """
        Analyze audio and transcript to detect emotional state
        
        Returns:
            BehaviorEvent with state, arousal, valence, and confidence
        """
        # Extract prosodic features
        prosody = self._extract_prosody_features(audio, sample_rate)
        
        # Calculate arousal and valence
        arousal = self._calculate_arousal(prosody)
        valence = self._calculate_valence(prosody, transcript)
        
        # Detect specific state
        state, confidence, triggers = self._detect_state(
            prosody, transcript, arousal, valence
        )
        
        # Create event
        event = BehaviorEvent(
            state=state,
            arousal=arousal,
            valence=valence,
            confidence=confidence,
            timestamp=datetime.now(),
            triggers=triggers
        )
        
        # Update history
        self.event_history.append(event)
        self.current_state = state
        
        # Update baseline if calm
        if state == EmotionalState.CALM and confidence > 0.7:
            self._update_baseline(prosody)
        
        return event
    
    def _extract_prosody_features(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> Dict:
        """Extract prosodic features from audio"""
        
        # Fundamental frequency (pitch)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sample_rate
        )
        f0_clean = f0[~np.isnan(f0)]
        
        # Energy (loudness)
        energy = librosa.feature.rms(y=audio)[0]
        
        # Speech rate estimation
        onset_env = librosa.onset.onset_strength(y=audio, sr=sample_rate)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sample_rate)[0]
        
        # Zero crossing rate (roughness indicator)
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        
        return {
            'f0_mean': float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0,
            'f0_std': float(np.std(f0_clean)) if len(f0_clean) > 0 else 0,
            'f0_min': float(np.min(f0_clean)) if len(f0_clean) > 0 else 0,
            'f0_max': float(np.max(f0_clean)) if len(f0_clean) > 0 else 0,
            'energy_mean': float(np.mean(energy)),
            'energy_std': float(np.std(energy)),
            'tempo': float(tempo),
            'zcr_mean': float(np.mean(zcr)),
            'duration': len(audio) / sample_rate
        }
    
    def _calculate_arousal(self, prosody: Dict) -> float:
        """
        Calculate arousal (activation level) from prosody
        
        High arousal indicators:
        - High pitch variance
        - Fast speech rate
        - High energy
        
        Returns: 0-1 (low to high arousal)
        """
        arousal_score = 0.0
        
        # Pitch variance contribution (0-0.4)
        if prosody['f0_std'] > self.thresholds['high_pitch_variance']:
            pitch_contribution = min(0.4, prosody['f0_std'] / 100)
            arousal_score += pitch_contribution
        
        # Speech rate contribution (0-0.3)
        if prosody['tempo'] > self.thresholds['fast_speech_rate']:
            rate_contribution = min(0.3, (prosody['tempo'] - 100) / 200)
            arousal_score += rate_contribution
        
        # Energy contribution (0-0.3)
        if prosody['energy_mean'] > self.thresholds['high_energy']:
            energy_contribution = min(0.3, prosody['energy_mean'] / 0.5)
            arousal_score += energy_contribution
        
        return min(1.0, arousal_score)
    
    def _calculate_valence(self, prosody: Dict, transcript: str) -> float:
        """
        Calculate valence (positive/negative affect)
        
        Positive indicators:
        - Rising pitch contour
        - Progress keywords
        - Moderate energy
        
        Negative indicators:
        - Falling pitch
        - Anxiety keywords
        - Very low/high energy
        
        Returns: -1 to +1 (negative to positive)
        """
        valence_score = 0.0
        
        # Keyword analysis
        transcript_lower = transcript.lower()
        
        # Negative keywords
        anxiety_count = sum(1 for word in self.anxiety_keywords if word in transcript_lower)
        if anxiety_count > 0:
            valence_score -= min(0.5, anxiety_count * 0.2)
        
        # Positive keywords
        progress_count = sum(1 for word in self.progress_keywords if word in transcript_lower)
        if progress_count > 0:
            valence_score += min(0.5, progress_count * 0.2)
        
        # Energy-based (too low or too high = negative)
        if prosody['energy_mean'] < self.thresholds['low_energy']:
            valence_score -= 0.3  # Withdrawal/shutdown
        elif prosody['energy_mean'] > self.thresholds['high_energy'] * 2:
            valence_score -= 0.2  # Overstimulation
        else:
            valence_score += 0.1  # Moderate energy is positive
        
        return max(-1.0, min(1.0, valence_score))
    
    def _detect_state(
        self,
        prosody: Dict,
        transcript: str,
        arousal: float,
        valence: float
    ) -> Tuple[EmotionalState, float, List[str]]:
        """
        Detect specific emotional state from features
        
        Returns:
            (state, confidence, triggers)
        """
        triggers = []
        
        # SHUTDOWN: Low arousal + negative valence + very low energy
        if arousal < 0.2 and valence < -0.3:
            if prosody['energy_mean'] < self.thresholds['low_energy']:
                triggers.append("very_low_energy")
            if prosody['duration'] > self.thresholds['long_pause']:
                triggers.append("long_silence")
            return EmotionalState.SHUTDOWN, 0.8, triggers
        
        # ANXIOUS: High arousal + negative valence
        if arousal > 0.6 and valence < 0:
            if prosody['f0_std'] > self.thresholds['high_pitch_variance']:
                triggers.append("high_pitch_variance")
            if any(word in transcript.lower() for word in self.anxiety_keywords):
                triggers.append("anxiety_keywords")
            if prosody['tempo'] > self.thresholds['fast_speech_rate']:
                triggers.append("rapid_speech")
            return EmotionalState.ANXIOUS, 0.8, triggers
        
        # HIGH_ENERGY: High arousal + any valence
        if arousal > 0.7:
            if prosody['energy_mean'] > self.thresholds['high_energy']:
                triggers.append("high_energy")
            if prosody['tempo'] > self.thresholds['fast_speech_rate']:
                triggers.append("fast_tempo")
            return EmotionalState.HIGH_ENERGY, 0.7, triggers
        
        # PROGRESS: Low arousal + positive valence
        if arousal < 0.4 and valence > 0.3:
            if any(word in transcript.lower() for word in self.progress_keywords):
                triggers.append("progress_keywords")
            triggers.append("calm_positive")
            return EmotionalState.PROGRESS, 0.7, triggers
        
        # CALM: Default baseline state
        if arousal < 0.4 and abs(valence) < 0.3:
            triggers.append("baseline")
            return EmotionalState.CALM, 0.6, triggers
        
        # UNKNOWN: Can't confidently classify
        return EmotionalState.UNKNOWN, 0.3, ["unclear"]
    
    def _update_baseline(self, prosody: Dict):
        """Update baseline prosody from calm samples"""
        if self.baseline_prosody is None:
            self.baseline_prosody = prosody.copy()
        else:
            # Exponential moving average
            alpha = 0.1
            for key in prosody:
                if key in self.baseline_prosody:
                    self.baseline_prosody[key] = (
                        alpha * prosody[key] + 
                        (1 - alpha) * self.baseline_prosody[key]
                    )
    
    def get_recent_events(self, n: int = 10) -> List[BehaviorEvent]:
        """Get most recent behavioral events"""
        return self.event_history[-n:]
    
    def is_dysregulated(self) -> bool:
        """Check if user is currently dysregulated"""
        return self.current_state in [
            EmotionalState.ANXIOUS,
            EmotionalState.HIGH_ENERGY,
            EmotionalState.SHUTDOWN
        ]
    
    def get_regulation_trend(self, window: int = 5) -> str:
        """
        Analyze recent events to detect regulation trend
        
        Returns: "improving", "stable", "declining", "unknown"
        """
        if len(self.event_history) < window:
            return "unknown"
        
        recent = self.event_history[-window:]
        
        # Count states
        calm_count = sum(1 for e in recent if e.state == EmotionalState.CALM)
        progress_count = sum(1 for e in recent if e.state == EmotionalState.PROGRESS)
        dysreg_count = sum(1 for e in recent if e.state in [
            EmotionalState.ANXIOUS, EmotionalState.HIGH_ENERGY, EmotionalState.SHUTDOWN
        ])
        
        # Trend analysis
        if progress_count > calm_count and dysreg_count == 0:
            return "improving"
        elif dysreg_count > calm_count:
            return "declining"
        elif calm_count >= window - 1:
            return "stable"
        else:
            return "unknown"


# Example usage
if __name__ == "__main__":
    import soundfile as sf
    
    # Create monitor
    monitor = BehaviorMonitor(user_id="test_user")
    
    # Simulate analysis
    # In real use, this would be actual audio
    dummy_audio = np.random.randn(16000) * 0.1  # 1 second at 16kHz
    
    event = monitor.analyze(
        audio=dummy_audio,
        sample_rate=16000,
        transcript="I am feeling nervous"
    )
    
    print(f"Detected state: {event.state.value}")
    print(f"Arousal: {event.arousal:.2f}")
    print(f"Valence: {event.valence:.2f}")
    print(f"Confidence: {event.confidence:.2f}")
    print(f"Triggers: {event.triggers}")
    print(f"Is dysregulated: {monitor.is_dysregulated()}")
