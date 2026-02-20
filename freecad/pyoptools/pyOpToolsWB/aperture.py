# -*- coding: utf-8 -*-
"""Classes used to define an aperture."""
from .feedback import FeedbackHelper
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
import FreeCAD
import FreeCADGui
import Part
from FreeCAD import Units

import pyoptools.raytrace.comp_lib as comp_lib
from pyoptools.raytrace.shape import Circular

from math import radians


class ApertureGUI(WBCommandGUI):
    def __init__(self):

        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "Aperture.ui"])

    @FeedbackHelper.with_error_handling("Aperture")
    def accept(self):
        inDiam = self.form.InD.value()
        outDiam = self.form.OutD.value()

        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()

        obj = InsertApp(inDiam, outDiam, ID="AP")
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1


class ApertureMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, ApertureGUI)

    def GetResources(self):
        return {
            "MenuText": "Aperture",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Aperture",
            "Pixmap": "",
        }


class AperturePart(WBPart):
    def __init__(self, obj, InD=10, OutD=50):
        WBPart.__init__(self, obj, "Aperture")

        # Todo: Mirar como se puede usar un quantity

        obj.addProperty(
            "App::PropertyLength", "InD", "Shape", "Aperture internal diameter"
        )
        obj.addProperty(
            "App::PropertyLength", "OutD", "Shape", "Aperture external diameter"
        )
        obj.InD = Units.Quantity("{} mm".format(InD))
        obj.OutD = Units.Quantity("{} mm".format(OutD))
        obj.ViewObject.ShapeColor = (1.0, 1.0, 1.0, 0.0)

    def execute(self, obj):

        obj.Shape = buildaperture(obj.InD, obj.OutD)

    def pyoptools_repr(self, obj):
        InD = obj.InD.Value
        OutD = obj.OutD.Value

        return comp_lib.Stop(Circular(OutD / 2.0), Circular(InD / 2.0))


def InsertApp(InD=10, OutD=25, ID=""):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    AperturePart(myObj, InD, OutD)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj


def buildaperture(InD, OutD):
    id = Part.makeCylinder(InD / 2.0, 0.1)
    od = Part.makeCylinder(OutD / 2.0, 0.1)
    id.translate(FreeCAD.Base.Vector(0, 0, -0.05))
    od.translate(FreeCAD.Base.Vector(0, 0, -0.05))
    t = od.cut(id)
    return t
