"""
GOECKOH - Inner Voice Engine
Generates first-person self-talk scripts and rewrites external language

This module implements:
1. First-Person Rewriter (converts external to internal language)
2. Cognitive Gating (calm first, then correct)
3. Calming script generation
4. Context-aware script selection
"""

import re
from typing import List, Dict, Tuple
from enum import Enum
from dataclasses import dataclass

class ScriptType(Enum):
    """Types of scripts the engine can generate"""
    CALMING = "calming"
    AFFIRMATION = "affirmation"
    CORRECTION = "correction"
    TEACHING = "teaching"
    PROGRESS = "progress"

@dataclass
class InnerVoiceScript:
    """A generated script for playback"""
    text: str
    script_type: ScriptType
    priority: int  # 1-5, higher = more urgent
    duration_estimate: float  # seconds

class InnerVoiceEngine:
    """
    The Inner Voice Engine transforms external language into first-person
    internal language and generates appropriate self-talk scripts.
    
    Key Innovation: Cognitive Gating
    When dysregulated (GCL < 0.6):
    1. First: Calming script ("I am safe. I can breathe.")
    2. Then: Correction ("I can say: [corrected phrase]")
    
    This prevents overwhelming the user with corrections during dysregulation.
    """
    
    def __init__(self):
        # First-person transformation rules
        self.pronoun_map = {
            'you': 'I',
            'your': 'my',
            'you\'re': 'I\'m',
            'you are': 'I am',
            'yourself': 'myself',
            'yours': 'mine',
        }
        
        # Calming scripts by severity
        self.calming_scripts = {
            'high': [
                "I am safe. I can breathe.",
                "I am here. I am okay.",
                "I can take my time.",
                "I am in control of my breathing."
            ],
            'medium': [
                "I can slow down.",
                "I am doing my best.",
                "I can take a break if I need to.",
                "I am learning."
            ],
            'low': [
                "I am ready.",
                "I can do this.",
                "I am calm.",
                "I am present."
            ]
        }
        
        # Affirmation templates
        self.affirmations = [
            "I said that well.",
            "I am getting better at this.",
            "I expressed myself clearly.",
            "I am proud of my progress.",
            "I am learning to speak my thoughts."
        ]
        
        # Correction templates
        self.correction_templates = {
            'simple': "I can say: {corrected}",
            'detailed': "I can say it this way: {corrected}",
            'encouraging': "I can say: {corrected}. I'm getting better."
        }
    
    def rewrite_first_person(self, text: str) -> str:
        """
        Rewrite text from second-person to first-person
        
        Examples:
            "You should calm down" → "I should calm down"
            "That's your problem" → "That's my problem"
            "You're doing great" → "I'm doing great"
        
        This is CRITICAL for therapeutic efficacy:
        - First-person = internal attribution (self-agency)
        - Second-person = external instruction (no agency)
        """
        rewritten = text
        
        # Sort by length (longest first) to handle multi-word phrases
        sorted_pronouns = sorted(
            self.pronoun_map.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for external, internal in sorted_pronouns:
            # Case-insensitive replacement with word boundaries
            pattern = r'\b' + re.escape(external) + r'\b'
            rewritten = re.sub(
                pattern,
                internal,
                rewritten,
                flags=re.IGNORECASE
            )
        
        # Handle sentence-initial capitalization
        if rewritten and rewritten[0].islower() and text[0].isupper():
            rewritten = rewritten[0].upper() + rewritten[1:]
        
        return rewritten
    
    def generate_calming_script(
        self,
        arousal: float,
        valence: float
    ) -> InnerVoiceScript:
        """
        Generate appropriate calming script based on state
        
        Args:
            arousal: 0-1 (low to high)
            valence: -1 to +1 (negative to positive)
            
        Returns:
            Calming script with priority
        """
        # Determine severity
        if arousal > 0.7 or valence < -0.5:
            severity = 'high'
            priority = 5
        elif arousal > 0.5 or valence < -0.2:
            severity = 'medium'
            priority = 4
        else:
            severity = 'low'
            priority = 3
        
        # Select script (rotate through available scripts)
        import random
        script_text = random.choice(self.calming_scripts[severity])
        
        # Estimate duration (rough: 2 words per second)
        duration = len(script_text.split()) / 2.0
        
        return InnerVoiceScript(
            text=script_text,
            script_type=ScriptType.CALMING,
            priority=priority,
            duration_estimate=duration
        )
    
    def generate_correction_script(
        self,
        original_text: str,
        corrected_text: str,
        gcl: float,
        arousal: float
    ) -> List[InnerVoiceScript]:
        """
        Generate correction script(s) with cognitive gating
        
        If GCL < 0.6 (dysregulated):
            1. First: Calming script
            2. Then: Simple correction
        
        If GCL >= 0.6 (regulated):
            1. Encouraging correction
        
        Args:
            original_text: What user said
            corrected_text: Corrected version
            gcl: Current Gated Coherence Level
            arousal: Current arousal level
            
        Returns:
            List of scripts in order of delivery
        """
        scripts = []
        
        # Rewrite correction to first-person
        corrected_first_person = self.rewrite_first_person(corrected_text)
        
        # If dysregulated, add calming script first
        if gcl < 0.6:
            calming = self.generate_calming_script(arousal, valence=0)
            scripts.append(calming)
            
            # Then simple correction
            template = self.correction_templates['simple']
            priority = 3
        else:
            # Regulated: use encouraging template
            template = self.correction_templates['encouraging']
            priority = 2
        
        # Generate correction script
        correction_text = template.format(corrected=corrected_first_person)
        duration = len(correction_text.split()) / 2.0
        
        correction_script = InnerVoiceScript(
            text=correction_text,
            script_type=ScriptType.CORRECTION,
            priority=priority,
            duration_estimate=duration
        )
        
        scripts.append(correction_script)
        
        return scripts
    
    def generate_affirmation(self, achievement: str = "general") -> InnerVoiceScript:
        """
        Generate positive affirmation for progress
        
        Used when:
        - User has successful utterance
        - User self-corrects
        - User shows improvement
        """
        import random
        
        # Select appropriate affirmation
        if achievement == "self_correction":
            text = "I corrected myself. I'm learning."
        elif achievement == "fluent":
            text = random.choice([
                "I said that clearly.",
                "I expressed myself well.",
                "I spoke fluently."
            ])
        else:
            text = random.choice(self.affirmations)
        
        duration = len(text.split()) / 2.0
        
        return InnerVoiceScript(
            text=text,
            script_type=ScriptType.AFFIRMATION,
            priority=2,
            duration_estimate=duration
        )
    
    def generate_teaching_script(
        self,
        concept: str,
        explanation: str
    ) -> InnerVoiceScript:
        """
        Generate teaching script for new concepts
        
        Only used when GCL > 0.6 (regulated)
        
        Example:
            concept: "past tense"
            explanation: "I can add 'ed' to show something already happened"
        """
        # Rewrite to first-person
        explanation_first_person = self.rewrite_first_person(explanation)
        
        text = f"About {concept}: {explanation_first_person}"
        duration = len(text.split()) / 2.0
        
        return InnerVoiceScript(
            text=text,
            script_type=ScriptType.TEACHING,
            priority=1,  # Low priority - only when regulated
            duration_estimate=duration
        )
    
    def select_appropriate_script(
        self,
        original_text: str,
        corrected_text: str,
        detected_errors: List[Dict],
        arousal: float,
        valence: float,
        gcl: float
    ) -> List[InnerVoiceScript]:
        """
        Main method: Select appropriate script(s) based on state
        
        Decision tree:
        1. If GCL < 0.3: ONLY calming
        2. If GCL 0.3-0.6: Calming + simple correction
        3. If GCL > 0.6: Encouraging correction (or affirmation if no errors)
        
        Args:
            original_text: User's utterance
            corrected_text: Corrected version
            detected_errors: List of errors
            arousal, valence, gcl: Current state
            
        Returns:
            List of scripts in delivery order
        """
        scripts = []
        
        # High dysregulation: ONLY calming
        if gcl < 0.3:
            calming = self.generate_calming_script(arousal, valence)
            scripts.append(calming)
            return scripts
        
        # No errors: affirmation
        if len(detected_errors) == 0:
            affirmation = self.generate_affirmation("fluent")
            scripts.append(affirmation)
            return scripts
        
        # Has errors: correction with possible calming
        correction_scripts = self.generate_correction_script(
            original_text,
            corrected_text,
            gcl,
            arousal
        )
        scripts.extend(correction_scripts)
        
        return scripts
    
    def format_for_display(self, scripts: List[InnerVoiceScript]) -> str:
        """
        Format scripts for display/logging
        
        Returns:
            Formatted string showing script sequence
        """
        lines = []
        for i, script in enumerate(scripts, 1):
            lines.append(f"{i}. [{script.script_type.value}] {script.text}")
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    engine = InnerVoiceEngine()
    
    print("=== INNER VOICE ENGINE EXAMPLES ===\n")
    
    # Example 1: First-person rewriting
    print("1. First-Person Rewriting:")
    original = "You should calm down"
    rewritten = engine.rewrite_first_person(original)
    print(f"   Original: {original}")
    print(f"   Rewritten: {rewritten}\n")
    
    # Example 2: High dysregulation (GCL < 0.3)
    print("2. High Dysregulation (GCL=0.2):")
    scripts = engine.select_appropriate_script(
        original_text="I wan go park",
        corrected_text="I want to go to the park",
        detected_errors=[{'type': 'phonemic'}],
        arousal=0.9,
        valence=-0.6,
        gcl=0.2
    )
    print(engine.format_for_display(scripts))
    print()
    
    # Example 3: Moderate state (GCL = 0.5)
    print("3. Moderate State (GCL=0.5):")
    scripts = engine.select_appropriate_script(
        original_text="I wan go park",
        corrected_text="I want to go to the park",
        detected_errors=[{'type': 'phonemic'}],
        arousal=0.6,
        valence=-0.2,
        gcl=0.5
    )
    print(engine.format_for_display(scripts))
    print()
    
    # Example 4: Regulated state (GCL = 0.8)
    print("4. Regulated State (GCL=0.8):")
    scripts = engine.select_appropriate_script(
        original_text="I wan go park",
        corrected_text="I want to go to the park",
        detected_errors=[{'type': 'phonemic'}],
        arousal=0.3,
        valence=0.5,
        gcl=0.8
    )
    print(engine.format_for_display(scripts))
    print()
    
    # Example 5: Perfect utterance
    print("5. Perfect Utterance (no errors):")
    scripts = engine.select_appropriate_script(
        original_text="I want to go to the park",
        corrected_text="I want to go to the park",
        detected_errors=[],
        arousal=0.3,
        valence=0.4,
        gcl=0.7
    )
    print(engine.format_for_display(scripts))
