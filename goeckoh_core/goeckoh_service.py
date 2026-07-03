"""
GOECKOH - Main Service Orchestrator
Connects all components and manages the therapeutic loop

This is the heart of Goeckoh - it orchestrates:
1. Voice Crystal (voice cloning & synthesis)
2. Behavior Monitor (emotional state detection)
3. Crystalline Heart (AMFL/GCL gating)
4. Inner Voice Engine (first-person scripts)

The complete therapeutic loop:
Speech → STT → Error Detection → Emotion Analysis → GCL Calculation
→ Script Generation → Voice Synthesis → Playback → Voice Harvesting → Progress Tracking
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from voice_crystal import VoiceCrystal
from behavior_monitor import BehaviorMonitor, EmotionalState
from crystalline_heart import CrystallineHeart, FeatureGate
from inner_voice_engine import InnerVoiceEngine, InnerVoiceScript

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TherapeuticTurn:
    """Represents one complete therapeutic interaction"""
    timestamp: datetime
    user_audio: np.ndarray
    user_transcript: str
    detected_errors: List[Dict]
    emotional_state: EmotionalState
    arousal: float
    valence: float
    coherence: float
    gcl: float
    feature_gate: FeatureGate
    generated_scripts: List[InnerVoiceScript]
    synthesized_audio: Optional[np.ndarray]
    duration_ms: float

class GoeckohService:
    """
    The main Goeckoh service that orchestrates all components
    
    This implements the complete therapeutic loop described in the research:
    - Captures speech
    - Detects errors and emotional state
    - Calculates GCL for gating
    - Generates appropriate first-person scripts
    - Synthesizes in user's voice
    - Plays back with cognitive gating
    - Tracks progress over time
    """
    
    def __init__(
        self,
        user_id: str,
        storage_path: str = "./goeckoh_data"
    ):
        self.user_id = user_id
        self.storage_path = storage_path
        
        # Initialize all components
        logger.info(f"Initializing Goeckoh for user: {user_id}")
        
        self.voice_crystal = VoiceCrystal(user_id, storage_path)
        self.behavior_monitor = BehaviorMonitor(user_id)
        self.crystalline_heart = CrystallineHeart(user_id)
        self.inner_voice = InnerVoiceEngine()
        
        # Session tracking
        self.session_active = False
        self.turn_history: List[TherapeuticTurn] = []
        
        logger.info("Goeckoh initialized successfully")
    
    def start_session(self):
        """Start a new therapeutic session"""
        self.session_active = True
        logger.info(f"Session started for user {self.user_id}")
    
    def stop_session(self):
        """End current therapeutic session"""
        self.session_active = False
        logger.info(f"Session ended for user {self.user_id}")
        logger.info(f"Total turns this session: {len(self.turn_history)}")
    
    def process_turn(
        self,
        audio: np.ndarray,
        sample_rate: int,
        transcript: str
    ) -> TherapeuticTurn:
        """
        Process one complete therapeutic turn
        
        This is the CORE METHOD that implements the full therapeutic loop.
        
        Args:
            audio: User's speech audio
            sample_rate: Audio sample rate (typically 16000)
            transcript: Transcribed text from STT
            
        Returns:
            TherapeuticTurn with all processing results
        """
        start_time = datetime.now()
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing turn: '{transcript}'")
        logger.info(f"{'='*60}")
        
        # Step 1: Detect errors (simplified - in production use proper error detection)
        detected_errors = self._detect_errors(transcript)
        corrected_text = self._correct_errors(transcript, detected_errors)
        logger.info(f"Errors detected: {len(detected_errors)}")
        if detected_errors:
            logger.info(f"Corrected: '{corrected_text}'")
        
        # Step 2: Analyze emotional state
        behavior_event = self.behavior_monitor.analyze(audio, sample_rate, transcript)
        logger.info(f"Emotional state: {behavior_event.state.value}")
        logger.info(f"Arousal: {behavior_event.arousal:.2f}, Valence: {behavior_event.valence:.2f}")
        
        # Step 3: Calculate coherence
        coherence = self.crystalline_heart.calculate_coherence(
            transcript=transcript,
            detected_errors=detected_errors,
            was_completed=True,  # TODO: Detect if utterance was completed
            audio_quality=0.8  # TODO: Calculate from audio
        )
        logger.info(f"Coherence: {coherence:.2f}")
        
        # Step 4: Update AMFL and calculate GCL
        amfl_snapshot = self.crystalline_heart.update(
            arousal=behavior_event.arousal,
            valence=behavior_event.valence,
            coherence=coherence
        )
        logger.info(f"GCL: {amfl_snapshot.gcl:.2f}")
        logger.info(f"Feature Gate: {amfl_snapshot.feature_gate.value}")
        
        # Step 5: Generate appropriate scripts
        scripts = self.inner_voice.select_appropriate_script(
            original_text=transcript,
            corrected_text=corrected_text,
            detected_errors=detected_errors,
            arousal=behavior_event.arousal,
            valence=behavior_event.valence,
            gcl=amfl_snapshot.gcl
        )
        logger.info(f"Generated {len(scripts)} script(s):")
        for i, script in enumerate(scripts, 1):
            logger.info(f"  {i}. [{script.script_type.value}] {script.text}")
        
        # Step 6: Synthesize in user's voice
        synthesized_audio = self._synthesize_scripts(scripts, audio, sample_rate)
        
        # Step 7: Harvest voice sample (if quality is good)
        if coherence > 0.6 and len(detected_errors) == 0:
            harvested = self.voice_crystal.harvest_voice(audio, sample_rate)
            if harvested:
                logger.info("Voice sample harvested for model improvement")
        
        # Create turn record
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        turn = TherapeuticTurn(
            timestamp=start_time,
            user_audio=audio,
            user_transcript=transcript,
            detected_errors=detected_errors,
            emotional_state=behavior_event.state,
            arousal=behavior_event.arousal,
            valence=behavior_event.valence,
            coherence=coherence,
            gcl=amfl_snapshot.gcl,
            feature_gate=amfl_snapshot.feature_gate,
            generated_scripts=scripts,
            synthesized_audio=synthesized_audio,
            duration_ms=duration_ms
        )
        
        self.turn_history.append(turn)
        logger.info(f"Turn processed in {duration_ms:.0f}ms")
        
        return turn
    
    def _detect_errors(self, transcript: str) -> List[Dict]:
        """
        Detect speech errors in transcript
        
        In production: Use proper error detection
        - Phoneme recognizer
        - Grammar checker
        - Context analysis
        
        For now: Simple heuristics
        """
        errors = []
        
        # Simple error detection examples
        if "wan" in transcript.lower() and "want" not in transcript.lower():
            errors.append({
                'type': 'phonemic',
                'word': 'wan',
                'correct': 'want',
                'position': transcript.lower().index('wan')
            })
        
        if "gonna" in transcript.lower():
            errors.append({
                'type': 'informal',
                'word': 'gonna',
                'correct': 'going to',
                'position': transcript.lower().index('gonna')
            })
        
        # Check for missing articles
        words = transcript.lower().split()
        for i, word in enumerate(words):
            if word in ['park', 'store', 'school'] and i > 0:
                if words[i-1] not in ['the', 'a', 'to']:
                    errors.append({
                        'type': 'grammar',
                        'word': word,
                        'suggestion': f'add article before {word}',
                        'position': i
                    })
        
        return errors
    
    def _correct_errors(self, transcript: str, errors: List[Dict]) -> str:
        """
        Apply corrections to transcript
        
        Returns corrected version
        """
        corrected = transcript
        
        for error in errors:
            if error['type'] == 'phonemic':
                corrected = corrected.replace(error['word'], error['correct'])
            elif error['type'] == 'informal':
                corrected = corrected.replace(error['word'], error['correct'])
            elif error['type'] == 'grammar':
                # More complex - would need proper grammar correction
                pass
        
        return corrected
    
    def _synthesize_scripts(
        self,
        scripts: List[InnerVoiceScript],
        original_audio: np.ndarray,
        sample_rate: int
    ) -> np.ndarray:
        """
        Synthesize all scripts in user's voice
        
        Returns concatenated audio
        """
        synthesized_segments = []
        
        for script in scripts:
            # Synthesize this script in user's voice
            audio_segment = self.voice_crystal.correct_and_synthesize(
                text=script.text,
                original_audio=original_audio,
                sample_rate=sample_rate,
                detected_errors=[]  # Scripts don't have errors
            )
            
            # Add pause between scripts (0.5 seconds)
            pause = np.zeros(int(sample_rate * 0.5))
            
            synthesized_segments.append(audio_segment)
            synthesized_segments.append(pause)
        
        # Concatenate all segments
        if synthesized_segments:
            return np.concatenate(synthesized_segments)
        else:
            return np.zeros(sample_rate)  # 1 second silence
    
    def get_session_summary(self) -> Dict:
        """Get summary of current/last session"""
        if len(self.turn_history) == 0:
            return {'status': 'no_turns'}
        
        # Calculate session statistics
        total_turns = len(self.turn_history)
        avg_gcl = np.mean([t.gcl for t in self.turn_history])
        
        # Count states
        state_counts = {}
        for turn in self.turn_history:
            state = turn.emotional_state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Progress indicators
        first_half_gcl = np.mean([t.gcl for t in self.turn_history[:len(self.turn_history)//2]]) if total_turns > 2 else avg_gcl
        second_half_gcl = np.mean([t.gcl for t in self.turn_history[len(self.turn_history)//2:]]) if total_turns > 2 else avg_gcl
        
        trend = "improving" if second_half_gcl > first_half_gcl + 0.1 else (
            "declining" if second_half_gcl < first_half_gcl - 0.1 else "stable"
        )
        
        return {
            'total_turns': total_turns,
            'avg_gcl': float(avg_gcl),
            'state_distribution': state_counts,
            'trend': trend,
            'voice_model_status': self.voice_crystal.get_model_status(),
            'progress_metrics': self.crystalline_heart.get_progress_metrics().__dict__
        }
    
    def export_clinical_data(self, filepath: str):
        """
        Export all data for clinical analysis
        
        Includes:
        - Turn-by-turn records
        - AMFL snapshots
        - Voice model status
        - Progress metrics
        """
        import json
        
        data = {
            'user_id': self.user_id,
            'export_timestamp': datetime.now().isoformat(),
            'session_summary': self.get_session_summary(),
            'turns': [
                {
                    'timestamp': t.timestamp.isoformat(),
                    'transcript': t.user_transcript,
                    'errors': t.detected_errors,
                    'emotional_state': t.emotional_state.value,
                    'arousal': t.arousal,
                    'valence': t.valence,
                    'coherence': t.coherence,
                    'gcl': t.gcl,
                    'feature_gate': t.feature_gate.value,
                    'scripts': [
                        {
                            'type': s.script_type.value,
                            'text': s.text
                        } for s in t.generated_scripts
                    ],
                    'duration_ms': t.duration_ms
                }
                for t in self.turn_history
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Clinical data exported to {filepath}")


# Example usage / Testing
if __name__ == "__main__":
    import soundfile as sf
    
    print("="*70)
    print("GOECKOH - Neuro-Acoustic Exocortex")
    print("Therapeutic Loop Demonstration")
    print("="*70)
    print()
    
    # Create service
    service = GoeckohService(user_id="demo_user", storage_path="./demo_data")
    service.start_session()
    
    # Simulate some turns
    print("\n" + "="*70)
    print("TURN 1: Dysregulated state with errors")
    print("="*70)
    
    # Simulated audio (in real use, this comes from microphone)
    audio1 = np.random.randn(16000) * 0.3  # 1 second, high energy
    turn1 = service.process_turn(
        audio=audio1,
        sample_rate=16000,
        transcript="I wan go park"
    )
    
    print("\n" + "="*70)
    print("TURN 2: Regulated state, no errors")
    print("="*70)
    
    audio2 = np.random.randn(16000) * 0.1  # 1 second, calm
    turn2 = service.process_turn(
        audio=audio2,
        sample_rate=16000,
        transcript="I want to go to the park"
    )
    
    # Get session summary
    print("\n" + "="*70)
    print("SESSION SUMMARY")
    print("="*70)
    
    summary = service.get_session_summary()
    print(f"Total turns: {summary['total_turns']}")
    print(f"Average GCL: {summary['avg_gcl']:.2f}")
    print(f"Trend: {summary['trend']}")
    print(f"State distribution: {summary['state_distribution']}")
    
    # Export clinical data
    service.export_clinical_data("./demo_data/clinical_export.json")
    
    service.stop_session()
    
    print("\n" + "="*70)
    print("Demo complete. Check ./demo_data/clinical_export.json for full data.")
    print("="*70)
