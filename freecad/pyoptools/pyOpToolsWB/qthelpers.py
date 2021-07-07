import FreeCAD
from PySide import QtCore, QtGui
import os

def outputDialog(msg, yn=False):
    """ Auxiliary function to create a dialog in pyside.

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

    diag = QtGui.QMessageBox(QtGui.QMessageBox.Information, 'Output', msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    if yn:
        diag.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    return diag.exec_() == QtGui.QMessageBox.Yes


def getUIFilePath(targetfile):
    """Helper function to find UI files"""

    return os.path.join(FreeCAD.ConfigGet("UserAppData"), "Mod",
                        "freecad-pyoptools", "freecad", "pyoptools",
                        "GUI",targetfile)
