# -*- coding: utf-8 -*-
"""Classes used to define a rectangular mirror."""
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


class RectMirrorGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()
        WBCommandGUI.__init__(self, [pw, mw, "RectMirror.ui"])

    def accept(self):
        Th = self.form.Thickness.value()
        Ref = self.form.Reflectivity.value()
        SX = self.form.SX.value()
        SY = self.form.SY.value()
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

        obj = InsertRectM(
            Ref, Th, SX, SY, ID="M1", matcat=matcat, matref=matref
        )
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class RectMirrorMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, RectMirrorGUI)

    def GetResources(self):
        return {
            "MenuText": "Rectangular Mirror",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Rectangular Mirror",
            "Pixmap": "",
        }


class RectMirrorPart(WBPart):
    def __init__(
        self, obj, Ref=100, Th=10, SX=50, SY=50, matcat="", matref=""
    ):

        WBPart.__init__(self, obj, "RectangularMirror")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyPercent",
            "Reflectivity",
            "Coating",
            "Mirror reflectivity",
        )
        obj.addProperty(
            "App::PropertyLength", "Thk", "Shape", "Mirror Thickness"
        )
        obj.addProperty(
            "App::PropertyLength", "Width", "Shape", "Mirror width"
        )
        obj.addProperty(
            "App::PropertyLength", "Height", "Shape", "Mirror height"
        )
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.Reflectivity = int(Ref)
        obj.Thk = Th
        obj.Width = SX
        obj.Height = SY
        obj.matcat = matcat
        obj.matref = matref

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5, 0.0)

    def pyoptools_repr(self, obj):

        material = getMaterial(obj.matcat, obj.matref)

        rm = comp_lib.RectMirror(
            (obj.Width.Value, obj.Height.Value, obj.Thk.Value),
            obj.Reflectivity / 100.0,
            material=material,
        )
        return rm

    def execute(self, obj):

        d = Part.makeBox(
            obj.Width.Value,
            obj.Height.Value,
            obj.Thk.Value,
            FreeCAD.Base.Vector(
                -obj.Width.Value / 2.0, -obj.Height.Value / 2.0, 0
            ),
        )
        obj.Shape = d


def InsertRectM(Ref=100, Th=10, SX=50, SY=50, ID="L", matcat="", matref=""):
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    RectMirrorPart(myObj, Ref, Th, SX, SY, matcat, matref)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj
