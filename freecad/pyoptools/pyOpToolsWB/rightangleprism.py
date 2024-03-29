# -*- coding: utf-8 -*-
"""Classes used to define a right angle prism."""
import FreeCAD
import FreeCADGui
import Part
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getMaterial

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians


class RightAnglePrismGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()
        WBCommandGUI.__init__(self, [pw, mw, "RightAnglePrism.ui"])

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
        rla = self.form.RefLegA.value()
        rlb = self.form.RefLegB.value()
        rhy = self.form.RefHypo.value()

        obj = InsertRAP(
            S,
            ID="RAP1",
            matcat=matcat,
            matref=matref,
            rla=rla,
            rlb=rlb,
            rhy=rhy,
        )
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class RightAnglePrismMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, RightAnglePrismGUI)

    def GetResources(self):
        return {
            "MenuText": "Right Angle Prism",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Right Angle Prism",
            "Pixmap": "",
        }


class RightAnglePrismPart(WBPart):
    def __init__(self, obj, S=50, matcat="", matref="", rla=0, rlb=0, rhy=0):

        WBPart.__init__(self, obj, "RightAnglePrism")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyLength", "S", "Shape", "Right Angle Prism side size "
        )
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.addProperty(
            "App::PropertyFloat", "rla", "Reflectivity", "Leg A Reflectivity"
        )
        obj.addProperty(
            "App::PropertyFloat", "rlb", "Reflectivity", "Leg B Reflectivity"
        )
        obj.addProperty(
            "App::PropertyFloat",
            "rhy",
            "Reflectivity",
            "Hypotenuse Reflectivity",
        )

        obj.S = S
        obj.matcat = matcat
        obj.matref = matref
        obj.rla = rla
        obj.rlb = rlb
        obj.rhy = rhy

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5, 0.0)

    def pyoptools_repr(self, obj):
        rla = obj.rla / 100.0
        rlb = obj.rlb / 100.0
        rhy = obj.rhy / 100.0
        S = obj.S.Value
        material = getMaterial(obj.matcat, obj.matref)
        
        rm = comp_lib.RightAnglePrism(
            S, S, material=material, reflectivity=rhy, reflega=rla, reflegb=rlb
        )
        return rm

    def execute(self, obj):

        l2 = obj.S.Value / 2.0

        v1 = FreeCAD.Base.Vector(l2, -l2, l2)
        v2 = FreeCAD.Base.Vector(l2, -l2, -l2)
        v3 = FreeCAD.Base.Vector(-l2, -l2, -l2)

        l1 = Part.makePolygon([v1, v2, v3, v1])
        F = Part.Face(Part.Wire(l1.Edges))
        d = F.extrude(FreeCAD.Base.Vector(0, 2 * l2, 0))

        obj.Shape = d


def InsertRAP(S=50, ID="RAP", matcat="", matref="", rla=0, rlb=0, rhy=0):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    RightAnglePrismPart(myObj, S, matcat, matref, rla, rlb, rhy)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj
