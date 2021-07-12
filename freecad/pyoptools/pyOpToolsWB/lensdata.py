# -*- coding: utf-8 -*-
"""Classes used to define a lens from a data list."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget

import Part

import pyoptools.raytrace.comp_lib as comp_lib
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget

import pyoptools.raytrace.mat_lib as matlib
from math import radians
from freecad.pyoptools import ICONPATH
from PySide2 import QtWidgets
from PySide2.QtCore import QLocale

from .sphericallens import buildlens
from math import isnan


class LensDataGUI(WBCommandGUI):
    def __init__(self):

        pw = placementWidget()
        self.mw = materialWidget()
        self.mw.ui.label.setText("")
        WBCommandGUI.__init__(self, [pw, "LensData.ui"])

        # In LensData.ui there is a layout called material that will be used as
        # holder for the material Widget.
        # TODO: Enable how to insert custom widgets in designer directly

        self.form.Material.addWidget(self.mw)

        self.form.addSurf.clicked.connect(self.addSurface)
        self.form.delSurf.clicked.connect(self.delSurface)

    def addSurface(self, *args):

        if not self.form.surfTable.selectedIndexes():
            i = self.form.surfTable.rowCount()
        else:
            i = self.form.surfTable.currentRow() + 1

        self.form.surfTable.insertRow(i)
        self.form.surfTable.selectRow(i)

        surfType = self.form.SurfType.currentText()
        item = QtWidgets.QTableWidgetItem(surfType)
        self.form.surfTable.setItem(i, 0, item)

        if self.form.Plane.isChecked():
            radius = "inf"
        else:
            radius = self.form.R.cleanText()

        item = QtWidgets.QTableWidgetItem(radius)
        self.form.surfTable.setItem(i, 1, item)

        thick = self.form.T.cleanText()
        item = QtWidgets.QTableWidgetItem(thick)
        self.form.surfTable.setItem(i, 2, item)

        semid = self.form.SD.cleanText()
        item = QtWidgets.QTableWidgetItem(semid)
        self.form.surfTable.setItem(i, 3, item)

        if self.form.NG.isChecked():
            matcat = ""
            matref = ""
        else:
            matcat = self.mw.Catalog.currentText()
            if matcat == "Value":
                matref = self.mw.Value.cleanText()
            else:
                matref = self.mw.Reference.currentText()

        item = QtWidgets.QTableWidgetItem(matcat)
        self.form.surfTable.setItem(i, 4, item)

        item = QtWidgets.QTableWidgetItem(matref)
        self.form.surfTable.setItem(i, 5, item)

    def delSurface(self, *args):

        if self.form.surfTable.selectedIndexes():
            i = self.form.surfTable.currentRow()
            self.form.surfTable.removeRow(i)

    def accept(self):

        surfType = []
        radius = []
        thick = []
        semid = []
        matcat = []
        matref = []

        lo = QLocale()

        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()

        for r in range(self.form.surfTable.rowCount()):
            surfType.append(self.form.surfTable.item(r, 0).text())
            radius.append(lo.toFloat(self.form.surfTable.item(r, 1).text())[0])
            thick.append(lo.toFloat(self.form.surfTable.item(r, 2).text())[0])
            semid.append(lo.toFloat(self.form.surfTable.item(r, 3).text())[0])
            matcat.append(self.form.surfTable.item(r, 4).text())
            matref.append(self.form.surfTable.item(r, 5).text())

        datalist = (surfType, radius, thick, semid, matcat, matref)

        obj = InsertLD(datalist, ID="L")
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class LensDataMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, LensDataGUI)

    def GetResources(self):
        return {
            "MenuText": "LensData",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Lenses from data editor",
            "Pixmap": "",
        }


class LensDataPart(WBPart):
    def __init__(self, obj, datalist):

        surfType, radius, thick, semid, matcat, matref = datalist

        WBPart.__init__(self, obj, "LensData")

        obj.addProperty(
            "App::PropertyStringList",
            "Type",
            "Shape",
            "List with the surfaces types",
        )
        obj.Type = surfType

        obj.addProperty(
            "App::PropertyFloatList",
            "Radius",
            "Shape",
            "List with the surfaces radius",
        )
        obj.Radius = radius

        obj.addProperty(
            "App::PropertyFloatList",
            "Thick",
            "Shape",
            "List with the material thickness",
        )
        obj.Thick = thick

        obj.addProperty(
            "App::PropertyFloatList",
            "SemiDiam",
            "Shape",
            "List with the surfaces semi diameters",
        )
        obj.SemiDiam = semid

        obj.addProperty(
            "App::PropertyStringList",
            "matcat",
            "Shape",
            "List with the material references",
        )
        obj.matcat = matcat

        obj.addProperty(
            "App::PropertyStringList",
            "matref",
            "Shape",
            "List with the material references",
        )
        obj.matref = matref

        obj.ViewObject.Transparency = 50

        obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0, 0.0)

    def execute(self, obj):
        Type = obj.Type
        Radius = obj.Radius
        Thick = obj.Thick
        SemiDiam = obj.SemiDiam
        matcat = obj.matcat
        matref = obj.matref

        l = list(zip(Type, Radius, Thick, SemiDiam, matcat, matref))
        lenses = []

        # In the total lens thickness, we do not take into account the last
        # surface thickness, as this one represent the image position
        TT = sum(Thick[:-1])
        p = -TT / 2

        # TODO: We are not checking that the last material is "" (meaning air)
        for n in range(1, len(l)):
            t0, r0, th0, s0, mc0, mt0 = l[n - 1]
            t1, r1, th1, s1, mc1, mt1 = l[n]

            if isnan(r0) or r0 == 0:
                c0 = 0
            else:
                c0 = 1 / r0

            if isnan(r1) or r1 == 0:
                c1 = 0
            else:
                c1 = 1 / r1
            if mt0 != "":
                L = buildlens(c0, c1, 2 * s0, th0)
                L.translate(FreeCAD.Base.Vector(0, 0, p + th0 / 2))
                lenses.append(L)
            p = p + th0

        L = lenses[0]

        for l in lenses[1:]:
            L = L.fuse(l)

        obj.Shape = L

    def pyoptools_repr(self, obj):
        Type = obj.Type
        Radius = obj.Radius
        Thick = obj.Thick
        SemiDiam = obj.SemiDiam
        matcat = obj.matcat
        matref = obj.matref

        l = list(zip(Type, Radius, Thick, SemiDiam, matcat, matref))

        return comp_lib.MultiLens(l)


def InsertLD(datalist, ID="L"):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    LensDataPart(myObj, datalist)

    # this is mandatory unless we code the ViewProvider too
    myObj.ViewObject.Proxy = 0
    FreeCAD.ActiveDocument.recompute()
    return myObj
