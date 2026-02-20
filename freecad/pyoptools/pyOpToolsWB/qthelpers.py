import FreeCAD
from PySide import QtCore, QtGui, QtWidgets
import os


def outputDialog(msg, yn=False):
    """Auxiliary function to create a dialog in pyside.

    Parameters
    ----------
    msg: Str
        String with the message to show.
    yn: Bool
        If True, the dialog will show Yes and No buttons, if False, only an
        accept button.

    Returns
    -------
    True if Yes button was present and pressed. False otherwise.
    """

    diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, "Output", msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    if yn:
        diag.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    return diag.exec_() == QtWidgets.QMessageBox.Yes


def getUIFilePath(targetfile):
    """Helper function to find UI files"""

    ui_file_path = os.path.join(
        FreeCAD.ConfigGet("UserAppData"),
        "Mod",
        "pyOpToolsWorkbench",
        "freecad",
        "pyoptools",
        "GUI",
        targetfile,
    )
    return ui_file_path
