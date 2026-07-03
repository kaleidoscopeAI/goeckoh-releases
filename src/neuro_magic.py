import math
import numpy as np


class KineticState:
    """
    Tracks accelerometer magnitude over time to estimate agitation.
    Agitation is normalized 0.0-1.0 against a learned baseline.
    """

    def __init__(self, max_history: int = 50):
        self.history: list[float] = []
        self.max_history = max_history
        self.baseline_energy = 0.0
        self.is_calibrating = True

    def update(self, x: float, y: float, z: float) -> float:
        energy = math.sqrt(x * x + y * y + z * z)
        self.history.append(energy)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        current_avg = sum(self.history) / len(self.history)

        if self.is_calibrating and len(self.history) == self.max_history:
            self.baseline_energy = current_avg
            self.is_calibrating = False
            return 0.0

        if self.is_calibrating:
            return 0.0

        delta = abs(current_avg - self.baseline_energy)
        agitation = min(1.0, delta / 2.0)  # >2.0 delta considered high agitation
        return agitation


class PsychoacousticDSP:
    """
    Generates subliminal binaural beats and warps timbre to nudge arousal.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate
        self.phase_l = 0.0
        self.phase_r = 0.0

    def generate_entrainment(self, duration_sec: float, target_state: str = "CALM") -> np.ndarray:
        """
        Returns interleaved stereo waveform with low-amplitude binaural beats.
        CALM (Alpha) = 10Hz diff, FOCUS (Beta) = 18Hz diff, else Theta-ish.
        """
        n_samples = int(self.sr * duration_sec)
        f_base = 200.0

        if target_state == "CALM":
            f_diff = 10.0
        elif target_state == "FOCUS":
            f_diff = 18.0
        else:
            f_diff = 4.0

        f_l = f_base
        f_r = f_base + f_diff
        t = np.arange(n_samples, dtype=np.float32) / self.sr

        wave_l = 0.05 * np.sin(2 * np.pi * f_l * t)
        wave_r = 0.05 * np.sin(2 * np.pi * f_r * t)

        stereo = np.zeros(n_samples * 2, dtype=np.float32)
        stereo[0::2] = wave_l
        stereo[1::2] = wave_r
        return stereo

    def apply_affective_filter(self, audio_data: np.ndarray, stress_level: float) -> np.ndarray:
        """
        One-pole low-pass whose cutoff closes as stress rises (softer voice).
        """
        cutoff = 1.0 - (stress_level * 0.5)  # 1.0=open, 0.5=muffled
        cutoff = max(0.1, min(1.0, cutoff))

        filtered = np.zeros_like(audio_data, dtype=np.float32)
        state = 0.0
        for i in range(len(audio_data)):
            state = cutoff * float(audio_data[i]) + (1.0 - cutoff) * state
            filtered[i] = state
        return filtered
