# -*- coding: utf-8 -*-
"""Classes used to define a pentaprism."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from pyOpToolsWB.widgets.placementWidget import placementWidget

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians, tan


class PentaPrismGUI(WBCommandGUI):
    def __init__(self):

        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "PentaPrism.ui"])

        self.form.Catalog.addItem("Value", [])
        for i in matlib.material.liblist:
            self.form.Catalog.addItem(i[0], sorted(i[1].keys()))
        self.form.Catalog.currentIndexChanged.connect(self.catalogChange)

    def catalogChange(self, *args):
        if args[0] == 0:
            self.form.Value.setEnabled(True)
        else:
            self.form.Value.setEnabled(False)

        while self.form.Reference.count():
            self.form.Reference.removeItem(0)
        self.form.Reference.addItems(self.form.Catalog.itemData(args[0]))

    def accept(self):
        S = self.form.S.value()
        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()
        matcat = self.form.Catalog.currentText()
        if matcat == "Value":
            matref = str(self.form.Value.value())
        else:
            matref = self.form.Reference.currentText()

        obj = InsertPP(S, ID="PP1", matcat=matcat, matref=matref)
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class PentaPrismMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, PentaPrismGUI)

    def GetResources(self):
        return {
            "MenuText": "Penta Prism",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Penta Prism",
            "Pixmap": "",
        }


class PentaPrismPart(WBPart):
    def __init__(self, obj, S=50, matcat="", matref=""):

        WBPart.__init__(self, obj, "PentaPrism")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyLength", "S", "Shape", "Penta Prism side size "
        )
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.S = S
        obj.matcat = matcat
        obj.matref = matref

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5, 0.0)

    def pyoptools_repr(self, obj):
        matcat = obj.matcat
        matref = obj.matref
        if matcat == "Value":
            material = float(matref.replace(",", "."))
        else:
            material = getattr(matlib.material, matcat)[matref]

        rm = comp_lib.PentaPrism(obj.S, material=material)
        return rm

    def execute(self, obj):
        import Part, FreeCAD

        l2 = obj.S.Value / 2.0

        q = 2 * l2 * tan(radians(22.5))
        v1 = FreeCAD.Base.Vector(l2, -l2, -l2)
        v2 = FreeCAD.Base.Vector(l2, -l2, l2)
        v3 = FreeCAD.Base.Vector(-l2, -l2, l2 + q)
        v4 = FreeCAD.Base.Vector(-l2 - q, -l2, l2)
        v5 = FreeCAD.Base.Vector(-l2, -l2, -l2)

        l1 = Part.makePolygon([v1, v2, v3, v4, v5, v1])
        F = Part.Face(Part.Wire(l1.Edges))
        d = F.extrude(FreeCAD.Base.Vector(0, 2 * l2, 0))

        obj.Shape = d


def InsertPP(S=50, ID="PP", matcat="", matref=""):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    PentaPrismPart(myObj, S, matcat, matref)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj
