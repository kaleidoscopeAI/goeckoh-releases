from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    SELF_PRESERVATION = 0
    LOW_RISK_INTERNAL = 1
    SCH_CORE = 2
    RESEARCH_LIGHT = 3
    EXTERNAL_AUTOMATION = 4
    INCOME_GENERATION = 5

class DRCRequestGate:
    def __init__(self, system_state):
        self.system_state = system_state

    def check_execution_permission(self, task_complexity: TaskComplexity) -> tuple[bool, str | None]:
        stability_band = self.system_state.get_stability_band()
        if stability_band == "MELTDOWN_RISK":
            return False, "RUN_IDENTITY_ATTRACTOR_FIELDS"
        elif stability_band == "OVERLOAD" and task_complexity.value > 1:
            return False, "INITIATE_REFLECTION_CYCLE"
        # Ethical enhancement: Always check APE
        if self.system_state.ape > 0.5:  # High error -> throttle
            return False, "HIGH_APE_THROTTLE"
        return True, None
