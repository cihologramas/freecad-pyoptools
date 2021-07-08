# -*- coding: utf-8 -*-
"""Classes used to define a doveprism."""
import FreeCAD
import FreeCADGui
import Part
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget
import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians


class DovePrismGUI(WBCommandGUI):
    def __init__(self):

        pw = placementWidget()
        mw = materialWidget()
        WBCommandGUI.__init__(self, [pw, mw, "DovePrism.ui"])

    def accept(self):
        S = self.form.S.value()
        L = self.form.L.value()
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

        obj = InsertDP(S, L, ID="DP1", matcat=matcat, matref=matref)
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class DovePrismMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, DovePrismGUI)

    def GetResources(self):
        return {
            "MenuText": "Dove Prism",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Dove Prism",
            "Pixmap": "",
        }


class DovePrismPart(WBPart):
    def __init__(self, obj, S=20, L=50, matcat="", matref=""):

        WBPart.__init__(self, obj, "PentaPrism")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyLength", "S", "Shape", "Dove Prism side size "
        )
        obj.addProperty(
            "App::PropertyLength", "L", "Shape", "Dove Prism lenght size "
        )
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.S = S
        obj.L = L
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

        rm = comp_lib.DovePrism(obj.S, obj.L, material=material)
        return rm

    def execute(self, obj):

        s2 = obj.S.Value / 2.0
        l2 = obj.L.Value / 2
        l2s = l2 - obj.S.Value

        v1 = FreeCAD.Base.Vector(-l2, -s2, -s2)
        v2 = FreeCAD.Base.Vector(-l2s, -s2, s2)
        v3 = FreeCAD.Base.Vector(l2s, -s2, s2)
        v4 = FreeCAD.Base.Vector(l2, -s2, -s2)

        l1 = Part.makePolygon([v1, v2, v3, v4, v1])
        F = Part.Face(Part.Wire(l1.Edges))
        d = F.extrude(FreeCAD.Base.Vector(0, 2 * s2, 0))

        obj.Shape = d


def InsertDP(S=20, L=50, ID="L", matcat="", matref=""):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    DovePrismPart(myObj, S, L, matcat, matref)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj
