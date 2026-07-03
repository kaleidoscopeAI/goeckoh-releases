# GOECKOH - Neuro-Acoustic Exocortex
## Complete System Architecture

## Mission Statement
Goeckoh is a revolutionary 100% offline Neuro-Acoustic Exocortex designed to trigger inner dialogue emergence in nonverbal and speech-limited individuals, particularly those with autism, TBI, and Alzheimer's. By playing corrected speech back in the user's exact voice, the system creates a self-correction loop that promotes neural development and self-agency.

## Core Innovation: The Self-Correction Hypothesis
**Key Principle**: Hearing corrected speech in one's own voice triggers the emergence of inner dialogue.

### Why This Works (Neuroscience):
1. **Self-Voice Congruence**: The brain recognizes its own voice uniquely
2. **Predictive Error Signal**: Hearing "what should have been said" creates optimal learning
3. **Agency Attribution**: Own-voice playback promotes internal attribution vs external instruction
4. **Neural Plasticity**: Repeated exposure strengthens speech motor pathways

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GOECKOH CORE SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   VOICE     │  │  BEHAVIOR    │  │   CRYSTALLINE    │  │
│  │  CRYSTAL    │  │   MONITOR    │  │      HEART       │  │
│  │             │  │              │  │                  │  │
│  │ • Clone     │  │ • Emotion    │  │ • AMFL Tracker  │  │
│  │ • Correct   │  │ • Dysreg     │  │ • GCL Gating    │  │
│  │ • Playback  │  │ • Events     │  │ • Coherence     │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                │                    │            │
│         └────────┬───────┴────────────────────┘            │
│                  │                                         │
│         ┌────────▼─────────┐                              │
│         │  INNER VOICE     │                              │
│         │     ENGINE       │                              │
│         │                  │                              │
│         │ • First-Person   │                              │
│         │   Rewriter       │                              │
│         │ • Prosody        │                              │
│         │   Transfer       │                              │
│         │ • Cognitive      │                              │
│         │   Gating         │                              │
│         └──────────────────┘                              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. VOICE CRYSTAL
**Purpose**: Clone, correct, and playback speech in user's exact voice

**Subcomponents**:
- **Voice Harvester**: Continuously captures user's voice samples
- **Phonemic Patcher**: Corrects mispronunciations at phoneme level
- **Prosody Transfer**: Maintains user's rhythm and energy
- **Dynamic Style Selection**: Adapts to emotional state
- **Adaptive TTS**: Generates speech in cloned voice

**Key Features**:
```python
class VoiceCrystal:
    def harvest_voice(audio_sample):
        """Continuously build voice model from user samples"""
        - Extract phonetic features
        - Build voice embedding
        - Update TTS model
        
    def correct_speech(input_text, detected_errors):
        """Apply phonemic corrections"""
        - Identify mispronunciations
        - Generate corrected phonemes
        - Preserve prosody
        
    def playback_in_own_voice(corrected_text, prosody_params):
        """Synthesize in user's exact voice"""
        - Apply voice embedding
        - Transfer prosody
        - Generate audio
```

### 2. BEHAVIOR MONITOR
**Purpose**: Detect emotional states and dysregulation events

**Tracked States**:
- `calm` - Baseline
- `anxious` - Elevated arousal
- `high_energy` - Excited/overstimulated
- `shutdown` - Withdrawal
- `progress` - Successful self-regulation

**Detection Methods**:
- Vocal prosody analysis (pitch, energy, rate)
- Speech pattern recognition
- Silence duration tracking
- Arousal/valence scoring

### 3. CRYSTALLINE HEART (AMFL System)
**Purpose**: Adaptive Memory-Formation Loop - tracks emotional development

**Components**:
- **Arousal Tracker**: Monitors activation level (0-1)
- **Valence Tracker**: Monitors positive/negative affect (-1 to +1)
- **Coherence Tracker**: Measures speech fluency/clarity (0-1)

**GCL (Gated Coherence Level)**:
```
GCL = (Coherence × 0.5) + ((1 - |Arousal - 0.5|) × 0.3) + (Valence × 0.2)

Thresholds:
- GCL < 0.3: High dysregulation - calming only
- GCL 0.3-0.6: Moderate - simple corrections
- GCL > 0.6: Stable - full features enabled
```

### 4. INNER VOICE ENGINE
**Purpose**: Generate first-person self-talk scripts

**First-Person Rewriter**:
```
Input: "You should calm down"
Output: "I am calming down"

Input: "That's wrong"
Output: "I can say it this way: [corrected]"
```

**Cognitive Gating**:
1. **Affective Regulation First**: "I am safe. I can breathe."
2. **Then Correction**: "I can say: [corrected phrase]"

---

## Data Flow

```
User Speaks
    ↓
STT Transcription
    ↓
Error Detection (phonemic, grammatical)
    ↓
Behavior Monitor Analysis (emotion, dysregulation)
    ↓
GCL Calculation (AMFL)
    ↓
├── If GCL < 0.3: Calming scripts only
├── If GCL 0.3-0.6: Simple corrections
└── If GCL > 0.6: Full corrections + teaching
    ↓
First-Person Rewrite
    ↓
Prosody Transfer (from user's input)
    ↓
Voice Crystal Synthesis (in user's voice)
    ↓
Playback to User
    ↓
Voice Harvesting (update voice model)
    ↓
AMFL Update (track progress)
```

---

## Therapeutic Use Cases

### Autism (Primary Target)
**Problem**: Echolalia, limited spontaneous speech, difficulty with self-initiated language
**Solution**: 
- Hears corrections in own voice → reduces "other-voice" resistance
- First-person scripts promote self-agency
- Gradual inner dialogue emergence

### TBI (Traumatic Brain Injury)
**Problem**: Aphasia, word-finding difficulty, speech motor impairment
**Solution**:
- Memory scaffolding via repeated own-voice corrections
- Prosody transfer maintains identity through recovery
- Phonemic patching aids motor relearning

### Alzheimer's
**Problem**: Declining language, word substitution, cognitive load
**Solution**:
- Familiar own-voice reduces confusion
- Simple first-person affirmations reduce anxiety
- Coherence tracking alerts caregivers to decline

---

## Privacy & Ethics (Non-Negotiable)

### 100% Offline Operation
- **No cloud services**
- **No data transmission**
- **All processing on-device**
- **Voice models stored locally encrypted**

### HIPAA-Ready Architecture
- Local-only storage
- Encrypted voice embeddings
- Caregiver consent gating
- Audit logs (local only)

### Autonomy Safeguards
- User can disable features
- Caregiver controls
- No covert monitoring
- Transparent operation

---

## Technical Stack

### Mobile (Flutter)
- **UI**: Material Design, accessibility-focused
- **STT**: Google Speech-to-Text (offline mode)
- **TTS**: Custom cloned voice (Coqui TTS / RVC)
- **ML**: TensorFlow Lite (on-device)
- **Storage**: SQLite + encrypted voice files

### Desktop (Python)
- **Processing**: NumPy, SciPy
- **ML**: PyTorch (local models)
- **Audio**: librosa, soundfile
- **Voice Cloning**: Coqui TTS, RVC (Retrieval-based Voice Conversion)

### Voice Cloning Pipeline
```python
1. Collect 10-30 seconds of user speech
2. Extract voice embedding (speaker encoder)
3. Fine-tune TTS model on embedding
4. Generate corrected speech in cloned voice
5. Continuously update model (adaptive harvesting)
```

---

## Implementation Priorities

### Phase 1: Core Loop (MVP)
1. ✅ Basic STT → correction → TTS
2. ✅ First-person rewriting
3. ✅ Simple voice cloning (even if imperfect)
4. ✅ Emotional state detection (basic)

### Phase 2: Therapeutic Optimization
1. ⏳ Advanced voice cloning (high fidelity)
2. ⏳ GCL gating system
3. ⏳ Phonemic patching
4. ⏳ Prosody transfer
5. ⏳ AMFL tracking

### Phase 3: AGI Integration
1. ⏳ Deep Reasoning Core
2. ⏳ Smart home control
3. ⏳ Cross-domain utility
4. ⏳ Long-term memory

---

## Success Metrics

### Clinical
- Inner dialogue emergence (self-reported / observed)
- Reduction in echolalia frequency
- Increase in spontaneous speech
- Improved self-regulation

### Technical
- Voice cloning accuracy (MOS score >4.0)
- Correction latency (<500ms)
- GCL prediction accuracy
- System uptime (offline reliability)

---

## Creator's Note

This system was built by Jacob Graham, father of a child on the autism spectrum, driven by the profound need to give nonverbal and speech-limited individuals the gift of inner dialogue and self-agency.

**Goeckoh is not just technology - it's hope made tangible.**

---

## File: `GOECKOH_ARCHITECTURE.md`
