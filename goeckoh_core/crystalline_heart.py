"""
GOECKOH - Crystalline Heart (AMFL System)
Adaptive Memory-Formation Loop for tracking emotional development

This module implements:
1. GCL (Gated Coherence Level) calculation
2. Arousal, Valence, Coherence tracking
3. Feature gating based on user state
4. Long-term progress tracking
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class FeatureGate(Enum):
    """Feature availability levels based on GCL"""
    CALMING_ONLY = "calming_only"  # GCL < 0.3
    SIMPLE_CORRECTIONS = "simple_corrections"  # GCL 0.3-0.6
    FULL_FEATURES = "full_features"  # GCL > 0.6

@dataclass
class AMFLSnapshot:
    """A snapshot of AMFL state at a moment in time"""
    arousal: float  # 0-1
    valence: float  # -1 to +1
    coherence: float  # 0-1
    gcl: float  # Calculated Gated Coherence Level
    feature_gate: FeatureGate
    timestamp: datetime

@dataclass
class ProgressMetrics:
    """Long-term progress tracking"""
    avg_gcl_last_day: float
    avg_gcl_last_week: float
    avg_coherence_trend: str  # "improving", "stable", "declining"
    dysregulation_frequency: float  # events per hour
    calm_duration_avg: float  # average seconds in calm state
    total_sessions: int
    inner_dialogue_markers: int  # Count of spontaneous speech

class CrystallineHeart:
    """
    The Crystalline Heart (AMFL) continuously tracks the user's
    emotional and cognitive state, calculating the Gated Coherence Level (GCL)
    which gates access to system features.
    
    Key Innovation: Adaptive Feature Gating
    - Low GCL (<0.3): Only calming scripts
    - Medium GCL (0.3-0.6): Simple corrections
    - High GCL (>0.6): Full system features
    
    This ensures the system never overwhelms a dysregulated user.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.snapshots: List[AMFLSnapshot] = []
        self.current_gcl = 0.5  # Start at moderate
        
        # GCL weights (from PDF specification)
        self.gcl_weights = {
            'coherence': 0.5,
            'arousal_stability': 0.3,
            'valence': 0.2
        }
        
        # GCL thresholds
        self.thresholds = {
            'calming_only': 0.3,
            'simple_corrections': 0.6,
            'full_features': 0.6
        }
        
        # Coherence calculation parameters
        self.coherence_factors = {
            'speech_clarity': 0.4,  # How clear/fluent is speech
            'error_rate': 0.3,  # Phonemic/grammatical errors
            'completion_rate': 0.3  # Finished vs interrupted utterances
        }
    
    def calculate_gcl(
        self,
        arousal: float,
        valence: float,
        coherence: float
    ) -> float:
        """
        Calculate Gated Coherence Level (GCL)
        
        Formula (from PDF):
        GCL = (Coherence × 0.5) + ((1 - |Arousal - 0.5|) × 0.3) + (Valence × 0.2)
        
        Args:
            arousal: 0-1 (low to high activation)
            valence: -1 to +1 (negative to positive)
            coherence: 0-1 (speech clarity/fluency)
            
        Returns:
            GCL score 0-1
        """
        # Coherence contribution (50%)
        coherence_contrib = coherence * self.gcl_weights['coherence']
        
        # Arousal stability contribution (30%)
        # Optimal arousal is 0.5 (moderate), deviation reduces score
        arousal_stability = 1 - abs(arousal - 0.5)
        arousal_contrib = arousal_stability * self.gcl_weights['arousal_stability']
        
        # Valence contribution (20%)
        # Normalize valence from [-1, 1] to [0, 1]
        valence_normalized = (valence + 1) / 2
        valence_contrib = valence_normalized * self.gcl_weights['valence']
        
        # Sum contributions
        gcl = coherence_contrib + arousal_contrib + valence_contrib
        
        return max(0.0, min(1.0, gcl))
    
    def calculate_coherence(
        self,
        transcript: str,
        detected_errors: List[Dict],
        was_completed: bool,
        audio_quality: float = 1.0
    ) -> float:
        """
        Calculate speech coherence score
        
        Factors:
        - Speech clarity (audio quality, intelligibility)
        - Error rate (phonemic/grammatical)
        - Completion rate (finished utterances)
        
        Returns:
            Coherence score 0-1
        """
        # Speech clarity from audio quality
        clarity = audio_quality * self.coherence_factors['speech_clarity']
        
        # Error rate (inverse - fewer errors = higher score)
        if len(transcript.split()) > 0:
            error_density = len(detected_errors) / len(transcript.split())
            error_score = max(0, 1 - error_density) * self.coherence_factors['error_rate']
        else:
            error_score = 0
        
        # Completion rate
        completion = (1.0 if was_completed else 0.0) * self.coherence_factors['completion_rate']
        
        coherence = clarity + error_score + completion
        
        return max(0.0, min(1.0, coherence))
    
    def update(
        self,
        arousal: float,
        valence: float,
        coherence: float
    ) -> AMFLSnapshot:
        """
        Update AMFL state and calculate new GCL
        
        Returns:
            Current AMFL snapshot with GCL and feature gate
        """
        # Calculate GCL
        gcl = self.calculate_gcl(arousal, valence, coherence)
        
        # Determine feature gate
        if gcl < self.thresholds['calming_only']:
            feature_gate = FeatureGate.CALMING_ONLY
        elif gcl < self.thresholds['simple_corrections']:
            feature_gate = FeatureGate.SIMPLE_CORRECTIONS
        else:
            feature_gate = FeatureGate.FULL_FEATURES
        
        # Create snapshot
        snapshot = AMFLSnapshot(
            arousal=arousal,
            valence=valence,
            coherence=coherence,
            gcl=gcl,
            feature_gate=feature_gate,
            timestamp=datetime.now()
        )
        
        # Store snapshot
        self.snapshots.append(snapshot)
        self.current_gcl = gcl
        
        return snapshot
    
    def get_current_gate(self) -> FeatureGate:
        """Get current feature gate level"""
        if len(self.snapshots) == 0:
            return FeatureGate.SIMPLE_CORRECTIONS  # Default to moderate
        return self.snapshots[-1].feature_gate
    
    def should_gate_feature(self, feature: str) -> bool:
        """
        Check if a specific feature should be gated
        
        Args:
            feature: "corrections", "teaching", "complex_speech", etc.
            
        Returns:
            True if feature should be blocked
        """
        current_gate = self.get_current_gate()
        
        # Define feature requirements
        feature_requirements = {
            'calming_scripts': FeatureGate.CALMING_ONLY,
            'simple_corrections': FeatureGate.SIMPLE_CORRECTIONS,
            'complex_corrections': FeatureGate.FULL_FEATURES,
            'teaching_mode': FeatureGate.FULL_FEATURES,
            'prosody_transfer': FeatureGate.SIMPLE_CORRECTIONS,
            'voice_cloning': FeatureGate.SIMPLE_CORRECTIONS,
        }
        
        required_gate = feature_requirements.get(feature, FeatureGate.FULL_FEATURES)
        
        # Gate hierarchy: CALMING_ONLY < SIMPLE_CORRECTIONS < FULL_FEATURES
        gate_levels = {
            FeatureGate.CALMING_ONLY: 0,
            FeatureGate.SIMPLE_CORRECTIONS: 1,
            FeatureGate.FULL_FEATURES: 2
        }
        
        return gate_levels[current_gate] < gate_levels[required_gate]
    
    def get_progress_metrics(self, days: int = 7) -> ProgressMetrics:
        """
        Calculate long-term progress metrics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            ProgressMetrics with trends and statistics
        """
        if len(self.snapshots) == 0:
            return ProgressMetrics(
                avg_gcl_last_day=0.5,
                avg_gcl_last_week=0.5,
                avg_coherence_trend="unknown",
                dysregulation_frequency=0,
                calm_duration_avg=0,
                total_sessions=0,
                inner_dialogue_markers=0
            )
        
        now = datetime.now()
        
        # Filter snapshots by time
        last_day = [s for s in self.snapshots if (now - s.timestamp) < timedelta(days=1)]
        last_week = [s for s in self.snapshots if (now - s.timestamp) < timedelta(days=days)]
        
        # Calculate averages
        avg_gcl_day = np.mean([s.gcl for s in last_day]) if last_day else 0.5
        avg_gcl_week = np.mean([s.gcl for s in last_week]) if last_week else 0.5
        
        # Coherence trend
        if len(last_week) > 10:
            first_half = last_week[:len(last_week)//2]
            second_half = last_week[len(last_week)//2:]
            
            avg_coherence_first = np.mean([s.coherence for s in first_half])
            avg_coherence_second = np.mean([s.coherence for s in second_half])
            
            if avg_coherence_second > avg_coherence_first + 0.1:
                coherence_trend = "improving"
            elif avg_coherence_second < avg_coherence_first - 0.1:
                coherence_trend = "declining"
            else:
                coherence_trend = "stable"
        else:
            coherence_trend = "unknown"
        
        # Dysregulation frequency (GCL < 0.3 events per hour)
        dysreg_events = [s for s in last_day if s.gcl < 0.3]
        hours_tracked = len(last_day) / 60 if last_day else 1  # Assuming ~1 sample per minute
        dysreg_freq = len(dysreg_events) / max(1, hours_tracked)
        
        # Calm duration (placeholder - needs state tracking)
        calm_duration_avg = 0  # TODO: Implement with state transitions
        
        # Inner dialogue markers (placeholder - needs speech analysis)
        inner_dialogue_markers = 0  # TODO: Detect spontaneous speech
        
        return ProgressMetrics(
            avg_gcl_last_day=float(avg_gcl_day),
            avg_gcl_last_week=float(avg_gcl_week),
            avg_coherence_trend=coherence_trend,
            dysregulation_frequency=float(dysreg_freq),
            calm_duration_avg=float(calm_duration_avg),
            total_sessions=len(self.snapshots),
            inner_dialogue_markers=inner_dialogue_markers
        )
    
    def get_current_status(self) -> Dict:
        """Get current AMFL status for display"""
        if len(self.snapshots) == 0:
            return {
                'gcl': 0.5,
                'feature_gate': 'simple_corrections',
                'coherence': 0.5,
                'arousal': 0.5,
                'valence': 0.0,
                'status': 'initializing'
            }
        
        latest = self.snapshots[-1]
        
        return {
            'gcl': latest.gcl,
            'feature_gate': latest.feature_gate.value,
            'coherence': latest.coherence,
            'arousal': latest.arousal,
            'valence': latest.valence,
            'status': 'active'
        }
    
    def export_data(self, filepath: str):
        """Export AMFL data for clinical analysis"""
        import json
        
        data = {
            'user_id': self.user_id,
            'snapshots': [
                {
                    'arousal': s.arousal,
                    'valence': s.valence,
                    'coherence': s.coherence,
                    'gcl': s.gcl,
                    'feature_gate': s.feature_gate.value,
                    'timestamp': s.timestamp.isoformat()
                }
                for s in self.snapshots
            ],
            'metrics': self.get_progress_metrics().__dict__
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Example usage
if __name__ == "__main__":
    # Create Crystalline Heart
    heart = CrystallineHeart(user_id="test_user")
    
    # Simulate updates
    print("Simulating AMFL updates...\n")
    
    # Scenario 1: High dysregulation
    snapshot1 = heart.update(arousal=0.8, valence=-0.5, coherence=0.3)
    print(f"Dysregulated state:")
    print(f"  GCL: {snapshot1.gcl:.2f}")
    print(f"  Gate: {snapshot1.feature_gate.value}")
    print(f"  Should gate teaching: {heart.should_gate_feature('teaching_mode')}\n")
    
    # Scenario 2: Moderate state
    snapshot2 = heart.update(arousal=0.5, valence=0.0, coherence=0.6)
    print(f"Moderate state:")
    print(f"  GCL: {snapshot2.gcl:.2f}")
    print(f"  Gate: {snapshot2.feature_gate.value}")
    print(f"  Should gate simple corrections: {heart.should_gate_feature('simple_corrections')}\n")
    
    # Scenario 3: Regulated state
    snapshot3 = heart.update(arousal=0.4, valence=0.5, coherence=0.8)
    print(f"Regulated state:")
    print(f"  GCL: {snapshot3.gcl:.2f}")
    print(f"  Gate: {snapshot3.feature_gate.value}")
    print(f"  Should gate teaching: {heart.should_gate_feature('teaching_mode')}\n")
    
    # Get progress metrics
    metrics = heart.get_progress_metrics()
    print(f"Progress Metrics:")
    print(f"  Avg GCL (week): {metrics.avg_gcl_last_week:.2f}")
    print(f"  Coherence trend: {metrics.avg_coherence_trend}")
    print(f"  Total sessions: {metrics.total_sessions}")
