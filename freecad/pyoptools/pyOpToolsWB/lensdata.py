# -*- coding: utf-8 -*-
from .wbcommand import *

import Part

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians
from freecad.pyoptools import ICONPATH
from PySide2 import QtWidgets
from PySide2.QtCore import QLocale

class LensDataGUI(WBCommandGUI):

    def __init__(self):

        WBCommandGUI.__init__(self,'LensData.ui')

        self.form.Catalog.addItem("Value", [])
        for i in matlib.material.liblist:
            self.form.Catalog.addItem(i[0], sorted(i[1].keys()))

        self.form.Catalog.currentIndexChanged.connect(self.catalogChange)
        self.form.addSurf.clicked.connect(self.addSurface)
        self.form.delSurf .clicked.connect(self.delSurface)

    def catalogChange(self, *args):
        if args[0] == 0:
            self.form.Value.setEnabled(True)
        else:
            self.form.Value.setEnabled(False)

        while self.form.Reference.count():
            self.form.Reference.removeItem(0)
        self.form.Reference.addItems(self.form.Catalog.itemData(args[0]))

    def addSurface(self, *args):

        if not self.form.surfTable.selectedIndexes():
            i = self.form.surfTable.rowCount()
        else:
            i = self.form.surfTable.currentRow()+1

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

        matcat = self.form.Catalog.currentText()
        if matcat == "Value":
            matref = self.form.Value.cleanText()
        else:
            matref = self.form.Reference.currentText()

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

        for r in range(self.form.surfTable.rowCount()):
            surfType.append(self.form.surfTable.item(r, 0).text())
            radius.append(lo.toFloat(self.form.surfTable.item(r, 1).text())[0])
            thick.append(lo.toFloat(self.form.surfTable.item(r, 2).text())[0])
            semid.append(lo.toFloat(self.form.surfTable.item(r, 3).text())[0])
            matcat.append(self.form.surfTable.item(r, 4).text())
            matref.append(self.form.surfTable.item(r, 5).text())

        datalist = (surfType, radius, thick, semid, matcat, matref)

        obj = InsertLD(datalist, ID="L")
#        m=FreeCAD.Matrix()
#        m.rotateX(radians(Xrot))
#        m.rotateY(radians(Yrot))
#        m.rotateZ(radians(Zrot))
#        m.move((X,Y,Z))
#        p1 = FreeCAD.Placement(m)
#        obj.Placement = p1
        FreeCADGui.Control.closeDialog()

class LensDataMenu(WBCommandMenu):

    def __init__(self):
        WBCommandMenu.__init__(self, LensDataGUI)

    def GetResources(self):
        return {"MenuText": "LensData",
                #"Accel": "Ctrl+M",
                "ToolTip": "Add Lenses from data editor",
                "Pixmap": ""}


class LensDataPart(WBPart):
    def __init__(self, obj, datalist):

        surfType, radius, thick, semid, matcat, matref = datalist

        WBPart.__init__(self, obj, "LensData")

        obj.addProperty("App::PropertyStringList",
                        "Type",
                        "Shape",
                        "List with the surfaces types")
        obj.Type = surfType

        obj.addProperty("App::PropertyFloatList",
                        "Radius",
                        "Shape",
                        "List with the surfaces radius")
        obj.Radius = radius

        obj.addProperty("App::PropertyFloatList",
                        "Thick",
                        "Shape",
                        "List with the material thickness")
        obj.Thick = thick

        obj.addProperty("App::PropertyFloatList",
                        "SemiDiam",
                        "Shape",
                        "List with the surfaces semi diameters")
        obj.SemiDiam = semid

        obj.addProperty("App::PropertyStringList",
                        "matcat",
                        "Shape",
                        "List with the material references")
        obj.matcat = matcat
        
        obj.addProperty("App::PropertyStringList",
                        "matref",
                        "Shape",
                        "List with the material references")
        obj.matref = matref

        obj.ViewObject.Transparency = 50

        obj.ViewObject.ShapeColor = (1., 1., 0., 0.)

    def execute(self,obj):
        pass
        #obj.Shape = buildlens(obj.CS1,obj.CS2,obj.D.Value,obj.Thk.Value)

    def pyoptools_repr(self,obj):
        #radius= obj.D.Value/2.
        #thickness=obj.Thk.Value
        #curvature_s1=obj.CS1
        #curvature_s2=obj.CS2
        #matcat=obj.matcat
        #matref=obj.matref
        #if matcat=="Value":
        #    material=float(matref.replace(",","."))
        #else:
        #    material=getattr(matlib.material,matcat)[matref]

        #return comp_lib.SphericalLens(radius=radius, thickness=thickness,
        #                          curvature_s1=curvature_s1, curvature_s2=curvature_s2,
        #                          material = material)
        pass


def InsertLD(datalist, ID="L"):
    import FreeCAD
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    LensDataPart(myObj, datalist)

    # this is mandatory unless we code the ViewProvider too
    myObj.ViewObject.Proxy = 0
    FreeCAD.ActiveDocument.recompute()
    return myObj

def buildlens(CS1,CS2,D,CT):
    pass
    #d=Part.makeCylinder(D/2.,CT+D)
    #d.translate(FreeCAD.Base.Vector(0,0,-(CT+D)/2))

    #if CS1==0:
    #    R1=1e6
    #else:
    #    R1=1./CS1
    #f1=Part.makeSphere(abs(R1))
    #f1.translate(FreeCAD.Base.Vector(0,0,R1-CT/2))

    #if CS2 ==0:
    #    R2 = 1e6
    #else:
    #    R2=1./CS2
    #f2=Part.makeSphere(abs(R2))
    #f2.translate(FreeCAD.Base.Vector(0,0,R2+CT/2))

    #if R1>0:
    #    t=d.common(f1)
    #else:
    #    t=d.cut(f1)
    #if R2>0:
    #    t=t.cut(f2)
    #else:
    #    t=t.common(f2)

    #return t
