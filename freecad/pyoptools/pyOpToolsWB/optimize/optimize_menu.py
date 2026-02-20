"""FreeCAD menu command for optical optimization.

This module provides OptimizeMenu, which integrates the optimization GUI
into the FreeCAD workbench menu system. The menu item is enabled only
when optical components exist in the active document.
"""

# Standard library imports
import os

# FreeCAD imports
import FreeCAD

# Local application imports
from freecad.pyoptools import ICONPATH
from ..wbcommand import WBCommandMenu
from .optimize_gui import OptimizeGUI


class OptimizeMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, OptimizeGUI)

    def GetResources(self):
        # Base tooltip
        tooltip = "Optimize component position to achieve optical goals (Shift+O)"

        # Add disabled reason if not active
        if not self.IsActive():
            if not FreeCAD.ActiveDocument:
                tooltip += " - Disabled: No document open"
            else:
                tooltip += " - Disabled: No optical components in document"

        return {
            "MenuText": "Optimize Position",
            "Accel": "Shift+O",
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "optimize-position.svg"),
        }

    def IsActive(self):
        """Enable button only when optical components exist in document.

        Returns:
            bool: True if at least one optical component exists, False otherwise
        """
        # Check if active document exists
        if not FreeCAD.ActiveDocument:
            return False

        # Check if any optical components exist (exclude propagation results)
        objs = FreeCAD.ActiveDocument.Objects
        optical_components = [
            obj
            for obj in objs
            if hasattr(obj, "ComponentType")
            and obj.ComponentType not in ["Propagation"]
        ]

        return bool(optical_components)

