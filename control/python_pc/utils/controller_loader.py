"""Utilities for discovering and loading controller modules."""

from __future__ import annotations

import os
from typing import Dict, List, Tuple


def get_available_controllers(
    controller_dir: str | None = None,
) -> Tuple[List[str], Dict[str, List[Tuple[str, str]]]]:
    """Return available controller modules and their parameters."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if controller_dir is None:
        controller_dir = os.path.join(base_dir, "..", "controllers")
        controller_dir = os.path.abspath(controller_dir)

    controllers: List[str] = []
    controller_params: Dict[str, List[Tuple[str, str]]] = {}

    if not os.path.isdir(controller_dir):
        raise FileNotFoundError(
            f"Controller directory not found: {controller_dir}"
        )

    for filename in os.listdir(controller_dir):
        if not filename.startswith("__") and filename.endswith(".py"):
            controller_name = filename[:-3]
            controllers.append(controller_name)
            params: List[Tuple[str, str]] = []
            with open(os.path.join(controller_dir, filename), "r") as f:
                lines = f.readlines()
            inside = False
            for line in lines:
                line = line.strip()
                if line == "# /VARS":
                    inside = True
                    continue
                if line == "# /ENDVARS":
                    break
                if inside and line.startswith("# /"):
                    var_line = line[3:].strip()
                    if ":" in var_line:
                        name, var_type = var_line.split(":", 1)
                        params.append((name.strip(), var_type.strip()))
                    else:
                        params.append((var_line.strip(), "float"))
            controller_params[controller_name] = params

    return controllers, controller_params


__all__ = ["get_available_controllers"]
