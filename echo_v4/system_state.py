from dataclasses import dataclass
import time
import sympy as sp  # For ODE solving (new: predictive modeling)
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemState:
    gcl: float = 0.8
    arousal: float = 0.3
    drc_status: str = "UNKNOWN"
    throttle_reason: str = ""
    last_gcl_update: float = 0.0
    ape: float = 0.0  # Auditory Prediction Error (new)

    def update_gcl(self, new_gcl: float, ape: float = 0.0):
        self.gcl = max(0.0, min(1.0, new_gcl - 0.05 * ape))  # Integrate predictive coding
        self.ape = ape
        self.last_gcl_update = time.time()

        # ODE lattice sim (improved: symbolic for precision)
        t = sp.symbols('t')
        E = sp.Function('E')(t)
        ode = sp.diff(E, t) - (0.1 * ape - 0.2 * E)  # Simplified diffusion
        
        try:
            solution = sp.dsolve(ode, E)
            logger.info(f"ODE Solution: {solution}")
        except Exception as e:
            logger.warning(f"Symbolic ODE solve failed: {e}")


    def get_stability_band(self) -> str:
        if self.gcl < 0.5: return "MELTDOWN_RISK"
        elif self.gcl < 0.7: return "OVERLOAD"
        elif self.gcl < 0.9: return "BASELINE"
        else: return "FLOW_STATE"
