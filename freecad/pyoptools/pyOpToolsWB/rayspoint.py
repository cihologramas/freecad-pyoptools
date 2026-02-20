# -*- coding: utf-8 -*-
"""Classes used to define a point source."""

import FreeCAD
import FreeCADGui
import Part
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from .feedback import FeedbackHelper

from pyoptools.misc.pmisc.misc import wavelength2RGB
import pyoptools.raytrace.ray.ray_source as rs_lib
from math import tan, radians
from FreeCAD import Units


class RaysPointGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "RaysPoint.ui"])

    @FeedbackHelper.with_error_handling("Point Source")
    def accept(self):
        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()

        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()

        nr = self.form.nr.value()
        na = self.form.na.value()
        distribution = self.form.RayDistribution.currentText()
        wavelength = self.form.wavelength.value()
        angle = self.form.ang.value()
        enabled = self.form.Enabled.isChecked()

        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))

        m.move((X, Y, Z))
        obj = InsertRPoint(nr, na, distribution, wavelength, angle, "S", enabled)

        p1 = FreeCAD.Placement(m)
        obj.Placement = p1


class RaysPointMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, RaysPointGUI)

    def GetResources(self):
        return {
            "MenuText": "Add Point Source",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Point Source",
            "Pixmap": "",
        }


class RaysPointPart(WBPart):
    def __init__(
        self,
        obj,
        nr=6,
        na=6,
        distribution="polar",
        wavelength=633,
        angle=30,
        enabled=True,
    ):
        WBPart.__init__(self, obj, "RaysPoint")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyIntegerConstraint", "nr", "Shape", "Number of rays (radial)"
        ).nr = (0, 0, 10000, 1)
        obj.addProperty(
            "App::PropertyIntegerConstraint", "na", "Shape", "Number of rays (angular)"
        ).na = (0, 0, 10000, 1)
        obj.addProperty(
            "App::PropertyString",
            "distribution",
            "Options",
            "Ray distribution (Polar for the moment)",
        )
        obj.addProperty(
            "App::PropertyLength", "wl", "Options", "Wavelength of the source"
        )
        obj.addProperty(
            "App::PropertyAngle", "angle", "Shape", "Source subtended angle"
        )
        obj.nr = nr
        obj.na = na
        obj.distribution = distribution.lower()
        obj.wl = Units.Quantity(
            "{} nm".format(wavelength)
        )  # wavelength is received in nm
        obj.angle = angle
        obj.Enabled = enabled

        r, g, b = wavelength2RGB(obj.wl.getValueAs("µm").Value)
        obj.ViewObject.ShapeColor = (r, g, b, 0.0)

    def onChanged(self, obj, prop):
        super().onChanged(obj, prop)

        if prop == "wl":
            r, g, b = wavelength2RGB(obj.wl.getValueAs("µm").Value)  # se pasa wl a um
            obj.ViewObject.ShapeColor = (r, g, b, 0.0)

    def pyoptools_repr(self, obj):
        dist = obj.distribution
        nr = obj.nr
        na = obj.na
        wl = obj.wl.getValueAs("µm").Value
        ang = obj.angle.getValueAs("rad").Value

        pla = obj.getGlobalPlacement()
        X, Y, Z = pla.Base
        RZ, RY, RX = pla.Rotation.toEuler()
        label = obj.Label
        if dist == "polar":
            r = rs_lib.point_source_p(
                origin=(X, Y, Z),
                direction=(radians(RX), radians(RY), radians(RZ)),
                span=ang,
                num_rays=(nr, na),
                wavelength=wl,
                label=label,
            )
        elif dist == "cartesian":
            r = rs_lib.point_source_c(
                origin=(X, Y, Z),
                direction=(radians(RX), radians(RY), radians(RZ)),
                span=(ang, ang),
                num_rays=(nr, na),
                wavelength=wl,
                label=label,
            )
        elif dist == "random":
            print("random ray distribution, not implemented yet")
        else:
            print("Warning ray distribution {} not recognized".format(dist))

        return r

    def execute(self, obj):
        dist = obj.distribution.lower()

        if dist not in ["polar", "cartesian"]:
            obj.distribution = "polar"
            print("Ray Distribution not understood, changing it to polar")

        if dist == "polar":
            # For small angles there is a big time delay in the cone draw. for
            # this reason the angle is limited to 5 degrees. This is only visual.

            if obj.angle < 5:
                ang = radians(5)
            else:
                ang = obj.angle.getValueAs("rad").Value
            r = 5 * tan(ang)
            d = Part.makeCone(0, r, 5)
            # d.translate(FreeCAD.Base.Vector(0,0,-0.5))
        else:  # Cartesian
            # Todo: Change to piramis instead of a cone
            r = 5 * tan(obj.angle.getValueAs("rad").Value)
            d = Part.makeCone(0, r, 5)
        obj.Shape = d


def InsertRPoint(
    nr=6, na=6, distribution="polar", wavelength=633, angle=30, ID="S", enabled=True
):
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    RaysPointPart(myObj, nr, na, distribution, wavelength, angle, enabled)
    myObj.ViewObject.Proxy = 0  # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj
