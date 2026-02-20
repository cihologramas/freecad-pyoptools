"""Enable/Disable commands for optical components.

This module provides FreeCAD menu commands to enable or disable selected
optical elements by setting their Enabled property to True or False.
"""

import os
import FreeCAD
import FreeCADGui
from freecad.pyoptools import ICONPATH


class EnableComponentsMenu:
    """Command to enable selected optical components."""

    def GetResources(self):
        """Return command metadata for FreeCAD menu system."""
        # Base tooltip
        tooltip = "Enable selected optical components (Ctrl+Shift+E)"

        # Add disabled reason if not active
        if not self.IsActive():
            if FreeCAD.ActiveDocument is None:
                tooltip += " - Disabled: No document open"
            else:
                tooltip += " - Disabled: No optical components selected"

        return {
            "MenuText": "Enable Components",
            "Accel": "Ctrl+Shift+E",
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "enable.svg"),
        }

    def IsActive(self):
        """Enable button only when optical components with Enabled property are selected.

        Returns:
            bool: True if valid components are selected, False otherwise
        """
        if FreeCAD.ActiveDocument is None:
            return False

        # Get current selection
        selection = FreeCADGui.Selection.getSelection()

        # Check if any selected objects have the Enabled property
        optical_components = [obj for obj in selection if hasattr(obj, "Enabled")]

        return len(optical_components) > 0

    def Activated(self):
        """Enable all selected optical components."""
        selection = FreeCADGui.Selection.getSelection()

        for obj in selection:
            if hasattr(obj, "Enabled"):
                obj.Enabled = True

        # Recompute document to trigger visual updates
        FreeCAD.ActiveDocument.recompute()


class DisableComponentsMenu:
    """Command to disable selected optical components."""

    def GetResources(self):
        """Return command metadata for FreeCAD menu system."""
        # Base tooltip
        tooltip = "Disable selected optical components (Ctrl+Shift+D)"

        # Add disabled reason if not active
        if not self.IsActive():
            if FreeCAD.ActiveDocument is None:
                tooltip += " - Disabled: No document open"
            else:
                tooltip += " - Disabled: No optical components selected"

        return {
            "MenuText": "Disable Components",
            "Accel": "Ctrl+Shift+D",
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "disable.svg"),
        }

    def IsActive(self):
        """Enable button only when optical components with Enabled property are selected.

        Returns:
            bool: True if valid components are selected, False otherwise
        """
        if FreeCAD.ActiveDocument is None:
            return False

        # Get current selection
        selection = FreeCADGui.Selection.getSelection()

        # Check if any selected objects have the Enabled property
        optical_components = [obj for obj in selection if hasattr(obj, "Enabled")]

        return len(optical_components) > 0

    def Activated(self):
        """Disable all selected optical components."""
        selection = FreeCADGui.Selection.getSelection()

        for obj in selection:
            if hasattr(obj, "Enabled"):
                obj.Enabled = False

        # Recompute document to trigger visual updates
        FreeCAD.ActiveDocument.recompute()
