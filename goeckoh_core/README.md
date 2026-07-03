# GOECKOH Core - Python Backend

## Complete Neuro-Acoustic Exocortex Implementation

This is the Python backend that implements the complete Goeckoh therapeutic loop.

---

## ✅ IMPLEMENTED COMPONENTS

### 1. Voice Crystal (`voice_crystal.py`)
- ✅ Voice harvesting framework
- ✅ Prosody extraction (F0, energy, tempo)
- ✅ Quality assessment
- ✅ Adaptive voice model updating
- ⏳ Needs: Coqui TTS integration for actual synthesis

### 2. Behavior Monitor (`behavior_monitor.py`)
- ✅ Emotional state detection (calm, anxious, high_energy, shutdown, progress)
- ✅ Arousal calculation (0-1)
- ✅ Valence calculation (-1 to +1)
- ✅ Multi-modal analysis (prosody + keywords + timing)
- ✅ Baseline tracking
- ✅ Regulation trend analysis

### 3. Crystalline Heart (`crystalline_heart.py`)
- ✅ GCL (Gated Coherence Level) calculation
- ✅ AMFL (Adaptive Memory-Formation Loop) tracking
- ✅ Feature gating (calming_only, simple_corrections, full_features)
- ✅ Progress metrics (daily/weekly GCL, coherence trends)
- ✅ Clinical data export

### 4. Inner Voice Engine (`inner_voice_engine.py`)
- ✅ First-person rewriting ("you" → "I")
- ✅ Cognitive gating (calm first, then correct)
- ✅ Calming script generation
- ✅ Correction script templates
- ✅ Affirmation generation
- ✅ Context-aware script selection

### 5. Main Orchestrator (`goeckoh_service.py`)
- ✅ Complete therapeutic loop implementation
- ✅ Turn-by-turn processing
- ✅ Session management
- ✅ Clinical data export
- ✅ Progress tracking
- ✅ All components integrated

---

## 🔄 THE COMPLETE THERAPEUTIC LOOP

```
User speaks → Audio captured
    ↓
STT transcription → "I wan go park"
    ↓
Error detection → [phonemic error in "wan"]
    ↓
Emotion analysis → State: ANXIOUS, Arousal: 0.8, Valence: -0.4
    ↓
Coherence calculation → 0.4 (moderate errors + dysregulation)
    ↓
GCL calculation → 0.35 (below threshold)
    ↓
Feature gating → SIMPLE_CORRECTIONS (calming + basic correction)
    ↓
Script generation:
  1. [CALMING] "I am safe. I can breathe."
  2. [CORRECTION] "I can say: I want to go to the park"
    ↓
Voice synthesis → Generate in user's EXACT voice
    ↓
Playback → User hears correction in own voice
    ↓
Voice harvesting → Update voice model (if good quality)
    ↓
Progress tracking → Update AMFL metrics
```

---

## 🚀 QUICK START

### 1. Install Dependencies

```bash
cd goeckoh_core
pip install -r ../requirements_goeckoh.txt
```

### 2. Test the System

```bash
python goeckoh_service.py
```

This will run a demonstration showing:
- Dysregulated turn (anxious state + errors)
- Regulated turn (calm state, no errors)
- Session summary
- Clinical data export

### 3. Use in Your Application

```python
from goeckoh_core.goeckoh_service import GoeckohService
import numpy as np

# Create service
service = GoeckohService(user_id="user123", storage_path="./data")
service.start_session()

# Process user speech
audio = np.array([...])  # Your audio data
transcript = "I wan go park"  # From STT

turn = service.process_turn(
    audio=audio,
    sample_rate=16000,
    transcript=transcript
)

# Access results
print(f"GCL: {turn.gcl}")
print(f"State: {turn.emotional_state}")
print(f"Scripts: {[s.text for s in turn.generated_scripts]}")

# Play synthesized audio
play_audio(turn.synthesized_audio)

# Get session summary
summary = service.get_session_summary()
print(summary)

service.stop_session()
```

---

## 📊 GCL THRESHOLDS & GATING

| GCL Range | Feature Gate | Available Features |
|-----------|--------------|-------------------|
| < 0.3 | CALMING_ONLY | Only calming scripts |
| 0.3 - 0.6 | SIMPLE_CORRECTIONS | Calming + basic corrections |
| > 0.6 | FULL_FEATURES | All features enabled |

**GCL Formula** (from research):
```
GCL = (Coherence × 0.5) + ((1 - |Arousal - 0.5|) × 0.3) + (Valence × 0.2)
```

Where:
- **Coherence**: Speech clarity/fluency (0-1)
- **Arousal**: Activation level (0-1, optimal = 0.5)
- **Valence**: Emotional tone (-1 to +1)

---

## 🎯 EMOTIONAL STATES

| State | Triggers | Response |
|-------|----------|----------|
| CALM | Low arousal, neutral valence | Standard corrections |
| ANXIOUS | High arousal + negative valence | Calming + simple correction |
| HIGH_ENERGY | High arousal (any valence) | Calming + redirect |
| SHUTDOWN | Low arousal + negative valence | Gentle affirmation only |
| PROGRESS | Low arousal + positive valence | Positive reinforcement |

---

## 🔬 CLINICAL DATA EXPORT

```python
service.export_clinical_data("patient_123_session.json")
```

Exports:
- Turn-by-turn transcripts
- Emotional states over time
- GCL progression
- Error patterns
- Voice model status
- Progress metrics

Perfect for:
- Clinical review
- Research analysis
- Progress reports for caregivers
- Efficacy studies

---

## 🎤 VOICE CLONING STATUS

**Current**: Placeholder (returns silence)

**To Enable**:

1. Install Coqui TTS:
```bash
pip install TTS
```

2. Update `voice_crystal.py`:
```python
from TTS.api import TTS

def _synthesize_with_voice_model(self, phonemes, prosody):
    # Initialize TTS
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
    
    # Fine-tune on user's voice embedding
    # ... (implementation details)
    
    # Generate audio
    audio = tts.tts(text, speaker_embedding=self.voice_embedding)
    return audio
```

3. Collect voice samples:
```python
# Need 10-30 seconds of clean user speech
for _ in range(20):
    crystal.harvest_voice(audio_sample, 16000)
```

---

## 📈 PROGRESS METRICS

The system tracks:

1. **GCL Trends**
   - Daily average
   - Weekly average
   - Improvement trajectory

2. **Coherence Development**
   - Trending up/stable/down
   - Error rate reduction

3. **Emotional Regulation**
   - Dysregulation frequency
   - Calm duration averages
   - State distribution

4. **Clinical Markers**
   - Inner dialogue emergence
   - Spontaneous speech increase
   - Self-correction instances

---

## 🧪 TESTING

Each component has standalone testing:

```bash
# Test individual components
python behavior_monitor.py
python crystalline_heart.py
python inner_voice_engine.py
python voice_crystal.py

# Test full system
python goeckoh_service.py
```

---

## 🔐 PRIVACY & ETHICS

**100% Offline Operation**:
- All processing local
- No cloud services
- No data transmission
- Voice models stored locally encrypted

**HIPAA-Ready**:
- Local-only storage
- Audit logging
- Access controls
- Data export for clinical review only

**User Autonomy**:
- Caregiver consent gating
- Transparent operation
- User can disable features
- No covert monitoring

---

## 🎯 NEXT STEPS

### Immediate
1. Integrate Coqui TTS for real voice cloning
2. Add proper phoneme recognizer
3. Improve error detection algorithms
4. Connect to Flutter frontend

### Short-term
1. Clinical pilot testing
2. Voice model quality improvement
3. GCL threshold tuning
4. Add more calming scripts

### Long-term
1. Smart home integration
2. Multi-language support
3. Caregiver dashboard
4. Cloud sync (optional, encrypted)

---

## 📚 RESEARCH FOUNDATION

This implementation is based on the research documented in:
- `GOECKOH_ARCHITECTURE.md`
- `Gemini-Voice, Speech, and Autistic Inner Dialogue.pdf`

**Key Principle**: Hearing corrected speech in one's own voice triggers inner dialogue emergence through:
1. Self-voice congruence (brain recognizes own voice)
2. Predictive error signal (optimal learning)
3. Agency attribution (internal vs external)
4. Neural plasticity (pathway strengthening)

---

## 👤 CREATOR

**Jacob Graham** - Father of a child on the autism spectrum

**Mission**: Give nonverbal and speech-limited individuals the gift of inner dialogue and self-agency.

---

## 📝 FILE MANIFEST

```
goeckoh_core/
├── __init__.py                   # Package init
├── voice_crystal.py              # Voice cloning & synthesis
├── behavior_monitor.py           # Emotional state detection
├── crystalline_heart.py          # AMFL/GCL system
├── inner_voice_engine.py         # First-person scripting
├── goeckoh_service.py            # Main orchestrator
└── README.md                     # This file
```

---

## ✅ STATUS

**Architecture**: ✅ Complete  
**Core Loop**: ✅ Implemented  
**Voice Cloning**: ⏳ Framework ready, needs TTS integration  
**Testing**: ✅ All components testable  
**Clinical Ready**: ⏳ Needs voice cloning + pilot testing  

**Estimated Time to Clinical Pilot**: 2-4 weeks (with TTS integration)

---

**This is real. This is buildable. This changes lives.**
