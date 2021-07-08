# -*- coding: utf-8 -*-
"""Classes used to define a light sensor."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians


class SensorGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "Sensor.ui"])

    def accept(self):
        width = self.form.Width.value()
        height = self.form.Height.value()
        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()

        obj = InsertSen(height, width, ID="SEN")

        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class SensorMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, SensorGUI)

    def GetResources(self):
        return {
            "MenuText": "Sensor",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Sensor",
            "Pixmap": "",
        }


class SensorPart(WBPart):
    def __init__(self, obj, height=10, width=10):

        WBPart.__init__(self, obj, "Sensor")
        obj.Proxy = self
        obj.addProperty("App::PropertyLength", "Width", "Shape", "Sensor width")
        obj.addProperty(
            "App::PropertyLength", "Height", "Shape", "Sensor height"
        )

        obj.Height = height
        obj.Width = width

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5, 0.0)

    def pyoptools_repr(self, obj):
        S = comp_lib.CCD((obj.Width, obj.Height))
        return S

    def execute(self, obj):
        import Part, FreeCAD

        d = Part.makePlane(
            obj.Width.Value,
            obj.Height.Value,
            FreeCAD.Base.Vector(
                -obj.Width.Value / 2.0, -obj.Height.Value / 2.0, 0
            ),
        )
        obj.Shape = d


def InsertSen(height=100, widht=100, ID="SEN"):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    SensorPart(myObj, height, widht)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj
