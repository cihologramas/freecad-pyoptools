# -*- coding: utf-8 -*-
"""Simple optimization of optical systems."""

from .wbcommand import *
import FreeCAD
from .pyoptoolshelpers import getActiveSystem
from numpy import std, array, sqrt
from scipy.optimize import minimize

from PySide import QtCore, QtGui


def outputDialog(msg):
    # Create a simple dialog QMessageBox
    # The first argument indicates the icon used: one of QtGui.QMessageBox.{NoIcon, Information, Warning, Critical, Question}
    diag = QtGui.QMessageBox(QtGui.QMessageBox.Information, "Output", msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    diag.exec_()


class OptimizeGUI(WBCommandGUI):
    def __init__(self):
        WBCommandGUI.__init__(self, "Optimize.ui")
        objs = FreeCAD.ActiveDocument.Objects
        opobjs = filter(lambda x: hasattr(x, "ComponentType"), objs)

        for i in opobjs:

            # No incluir las fuentes solo los elementos
            if i.ComponentType not in ["RaysPoint", "RaysPar"]:
                self.form.Element.addItem(i.Label, i)
            if i.ComponentType == "Sensor":
                self.form.Sensor.addItem(i.Label, i)

        # add some possible solvers supported by scipy.minimize
        solvers = [
            "Nelder-Mead",
            "Powell",
            "CG",
            "BFGS",
            "L-BFGS-B",
            "TNC",
            "COBYLA",
            "SLSQP",
            "trust-constr",
        ]
        self.form.Solver.addItems(solvers)

    def accept(self):

        el = self.form.Element.currentText()
        sen = self.form.Sensor.currentText()
        solver = self.form.Solver.currentText()

        if self.form.X.isChecked():
            ax = "X"
        elif self.form.Y.isChecked():
            ax = "Y"
        else:
            ax = "Z"

        S, rays = getActiveSystem()
        C, P, D = S.complist[el]

        if ax == "X":
            d = P[0]
        elif ax == "Y":
            d = P[1]
        else:
            d = P[2]

        if self.form.Collimation.isChecked():
            mini = minimize(opt_col, d, (el, sen, ax), method=solver)
            
        elif self.form.SpotSize.isChecked():
            mini =  minimize(opt_spot, d, (el, sen, ax), method=solver)
            
        elif self.form.XSize.isChecked():
            mini = minimize(opt_x, d, (el, sen, ax), method=solver)
            
        elif self.form.YSize.isChecked():
            mini = minimize(opt_y, d, (el, sen, ax), method=solver)
            
        outputDialog(
                 "Optimum {} Position for element {} = {} \n function value = {}".format(
                    ax, el, mini.x, mini.fun
                ))
        FreeCADGui.Control.closeDialog()


def opt_col(d, el="", sen="", ax="Z"):
    print(d)
    S, rays = getActiveSystem()
    C, P, D = S.complist[el]

    if ax == "X":
        P[0] = d
    elif ax == "Y":
        P[1] = d
    else:
        P[2] = d
    S.complist[el] = C, P, D

    S.ray_add(rays)
    S.propagate()

    X, Y, D = S[sen][0].get_optical_path_data()
    return std(D)


def opt_spot(d, el="", sen="", ax="Z"):
    print(d)
    S, rays = getActiveSystem()
    C, P, D = S.complist[el]

    if ax == "X":
        P[0] = d
    elif ax == "Y":
        P[1] = d
    else:
        P[2] = d
    S.complist[el] = C, P, D

    S.ray_add(rays)
    S.propagate()

    X, Y, D = S[sen][0].get_optical_path_data()

    X = array(X)
    Y = array(Y)

    # Centrar en X y Y y encontrar el radio promedio
    X = X - X.mean()
    Y = Y - Y.mean()
    r = sqrt(X ** 2 + Y ** 2)
    return r.mean()


def opt_x(d, el="", sen="", ax="Z"):
    print(d)
    S, rays = getActiveSystem()
    C, P, D = S.complist[el]

    if ax == "X":
        P[0] = d
    elif ax == "Y":
        P[1] = d
    else:
        P[2] = d
    S.complist[el] = C, P, D

    S.ray_add(rays)
    S.propagate()

    X, Y, D = S[sen][0].get_optical_path_data()

    X = array(X)
    Y = array(Y)

    # Centrar en X y encontrar el radio X promedio
    X = X - X.mean()
    r = sqrt(X ** 2)
    return r.mean()


def opt_y(d, el="", sen="", ax="Z"):
    print(d)
    S, rays = getActiveSystem()
    C, P, D = S.complist[el]

    if ax == "X":
        P[0] = d
    elif ax == "Y":
        P[1] = d
    else:
        P[2] = d
    S.complist[el] = C, P, D

    S.ray_add(rays)
    S.propagate()

    X, Y, D = S[sen][0].get_optical_path_data()

    X = array(X)
    Y = array(Y)

    # Centrar en Y y encontrar el radio Y promedio
    Y = Y - Y.mean()
    r = sqrt(Y ** 2)
    return r.mean()


class OptimizeMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, OptimizeGUI)

    def GetResources(self):
        return {
            "MenuText": "Optimize",
            # "Accel": "Ctrl+M",
            "ToolTip": "Optimize System",
            "Pixmap": "",
        }
