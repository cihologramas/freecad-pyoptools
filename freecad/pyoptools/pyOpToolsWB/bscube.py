# -*- coding: utf-8 -*-
"""Classes used to define a beam splitting cube."""
import FreeCAD
import FreeCADGui
import Part
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians


class BSCubeGUI(WBCommandGUI):
    def __init__(self):

        pw = placementWidget()
        mw = materialWidget()
        WBCommandGUI.__init__(self, [pw, mw, "BSCube.ui"])

    def accept(self):
        S = self.form.S.value()
        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()
        Ref = self.form.Reflectivity.value()
        matcat = self.form.Catalog.currentText()
        if matcat == "Value":
            matref = str(self.form.Value.value())
        else:
            matref = self.form.Reference.currentText()

        obj = InsertBSC(S, Ref, ID="BS1", matcat=matcat, matref=matref)
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class BSCubeMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, BSCubeGUI)

    def GetResources(self):
        return {
            "MenuText": "Beam Splitting Cube",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Beam Splitting Cube",
            "Pixmap": "",
        }


class BSCubePart(WBPart):
    def __init__(self, obj, S=50, Ref=100, matcat="", matref=""):

        WBPart.__init__(self, obj, "BSCube")
        obj.Proxy = self
        obj.addProperty("App::PropertyLength", "S", "Shape", "Cube side size ")
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.addProperty(
            "App::PropertyPercent",
            "Reflectivity",
            "Coating",
            "Mirror reflectivity",
        )
        obj.S = S
        obj.Reflectivity = Ref
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

        rm = comp_lib.BeamSplitingCube(
            obj.S.Value, obj.Reflectivity / 100.0, material=material
        )
        return rm

    def execute(self, obj):

        l2 = obj.S.Value / 2.0

        v1 = FreeCAD.Base.Vector(l2, -l2, -l2)
        v2 = FreeCAD.Base.Vector(l2, -l2, l2)
        v3 = FreeCAD.Base.Vector(-l2, -l2, l2)
        v4 = FreeCAD.Base.Vector(-l2, -l2, -l2)

        l1 = Part.makePolygon([v1, v2, v3, v1, v3, v4, v1])
        F = Part.Face(Part.Wire(l1.Edges))
        d = F.extrude(FreeCAD.Base.Vector(0, 2 * l2, 0))

        obj.Shape = d


def InsertBSC(S=50, Ref=100, ID="PP", matcat="", matref=""):

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    BSCubePart(myObj, S, Ref, matcat, matref)
    myObj.ViewObject.Proxy = (
        0
    )  # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj
