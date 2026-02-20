import FreeCAD


class WipeMenu:
    """
    Command to wipe (erase propagations and rays) from the system
    """

    def GetResources(self):
        from freecad.pyoptools import ICONPATH
        import os

        # Base tooltip
        tooltip = "Delete ray propagation visualization (Alt+W)"

        # Add disabled reason if not active
        if not self.IsActive():
            if FreeCAD.ActiveDocument is None:
                tooltip += " - Disabled: No document open"
            else:
                tooltip += " - Disabled: No ray propagations to delete"

        return {
            "MenuText": "Wipe",
            "Accel": "Alt+W",
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "wipe.svg"),
        }

    def IsActive(self):
        """
        Enable button only when there are propagations to delete.

        Returns:
            bool: True if propagations exist, False otherwise
        """
        if FreeCAD.ActiveDocument is None:
            return False

        # Check if any propagation objects exist
        objs = FreeCAD.ActiveDocument.Objects
        propagations = [
            obj
            for obj in objs
            if hasattr(obj, "ComponentType") and obj.ComponentType == "Propagation"
        ]

        return len(propagations) > 0

    def Activated(self):
        from PySide import QtCore, QtGui, QtWidgets

        # Create confirmation dialog with proper title
        diag = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Question,
            "Wipe Propagations",
            "Are you sure you want to delete all ray propagation visualizations?",
        )
        diag.setWindowModality(QtCore.Qt.ApplicationModal)
        diag.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        yn = diag.exec_() == QtWidgets.QMessageBox.Yes

        if yn:
            objs = FreeCAD.ActiveDocument.Objects
            todelete = []
            for obj in objs:
                if hasattr(obj, "ComponentType"):
                    if obj.ComponentType == "Propagation":
                        print("removing Propagation")
                        # Use the internal object name for reliable deletion.
                        todelete.append(obj.Name)
                        continue
            for obj in todelete:
                FreeCAD.ActiveDocument.removeObject(obj)
