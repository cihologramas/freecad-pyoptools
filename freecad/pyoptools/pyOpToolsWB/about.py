# -*- coding: utf-8 -*-
"""About dialog for the pyOpTools workbench."""

import os
import FreeCAD
import FreeCADGui
from PySide import QtWidgets, QtGui


class AboutMenu:
    def GetResources(self):
        from freecad.pyoptools import ICONPATH
        return {
            "MenuText": "About pyOpTools Workbench",
            "ToolTip": "Show version information for the pyOpTools workbench and library",
            "Pixmap": os.path.join(ICONPATH, "pyoptools.png"),
        }

    def IsActive(self):
        return True

    def Activated(self):
        from freecad.pyoptools import __version__ as wb_version, ICONPATH

        # Get pyoptools library version at runtime
        try:
            import pyoptools
            lib_version = getattr(pyoptools, "__version__", "unknown")
        except ImportError:
            lib_version = "not installed"

        msg = (
            f"<b>pyOpTools Workbench</b><br>"
            f"Workbench version: <b>{wb_version}</b><br><br>"
            f"pyoptools library version: <b>{lib_version}</b>"
        )

        icon = QtGui.QIcon(os.path.join(ICONPATH, "pyoptools.png"))
        mw = FreeCADGui.getMainWindow()

        dlg = QtWidgets.QMessageBox(mw)
        dlg.setWindowTitle("About pyOpTools Workbench")
        dlg.setText(msg)
        dlg.setWindowIcon(icon)
        dlg.setIconPixmap(icon.pixmap(64, 64))
        dlg.exec_()
