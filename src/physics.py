import time
import math


class CrystallineHeart:
    """
    Bio-mimetic affective safety regulator.
    Combines audio RMS, latency, and motion into a single stress scalar.
    """

    def __init__(self):
        self.gcl = 1.0  # Global Coherence Level (1.0 = calm)
        self.stress_heat = 0.0
        self.kinetic_stress = 0.0
        self.stress_bucket = 0.0
        self.last_tick = time.time()

    def pulse(self, rms_energy: float, latency_ms: float, kinetic_agitation: float):
        now = time.time()
        dt = max(1e-3, now - self.last_tick)
        self.last_tick = now

        self.kinetic_stress = kinetic_agitation

        heat_influx = (rms_energy * 0.8) + (max(0.0, latency_ms - 300.0) / 100.0) + (kinetic_agitation * 2.0)
        cooling_rate = 0.4 * dt
        self.stress_heat = max(0.0, self.stress_heat + heat_influx - cooling_rate)

        # Optional additional bucket for hard gating
        stress_increase = (rms_energy * 0.4) + (max(0.0, latency_ms - 200.0) / 100.0) + (kinetic_agitation * 2.0)
        self.stress_bucket = max(0.0, min(100.0, self.stress_bucket + stress_increase - 0.3))

        self.gcl = 1.0 / (1.0 + (self.stress_heat / 10.0))
        is_safe = self.gcl > 0.4 and self.stress_bucket < 90.0
        return self.gcl, is_safe
