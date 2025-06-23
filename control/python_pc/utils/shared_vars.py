from multiprocessing import Value
from typing import Dict
import multiprocessing

from typing import Any

def create_shared_vars() -> Dict[str, Any]:
    return {
        "position": Value("d", 0.0),
        "angle": Value("d", 0.0),
        "control_signal": Value("d", 0.0),
        "execution_time": Value("d", 0.0),
        "desired_angle": Value("d", 0.0),
    }
