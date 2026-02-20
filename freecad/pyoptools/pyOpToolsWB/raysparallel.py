# -*- coding: utf-8 -*-
"""Classes used to define a beam of parallel rays."""

import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from .feedback import FeedbackHelper

from pyoptools.misc.pmisc.misc import wavelength2RGB
import pyoptools.raytrace.ray.ray_source as rs_lib
from FreeCAD import Units
from math import radians


class RaysParallelGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "RaysParallel.ui"])

    @FeedbackHelper.with_error_handling("Parallel Rays")
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
        enabled = self.form.Enabled.isChecked()

        D = self.form.D.value()
        m = FreeCAD.Matrix()

        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))

        m.move((X, Y, Z))
        obj = InsertRPar(nr, na, distribution, wavelength, D, "S", enabled)

        p1 = FreeCAD.Placement(m)
        obj.Placement = p1


class RaysParallelMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, RaysParallelGUI)

    def GetResources(self):
        return {
            "MenuText": "Add Parallel Ray Source",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Parallel Ray Source",
            "Pixmap": "",
        }


class RaysParPart(WBPart):
    def __init__(
        self, obj, nr=6, na=6, distribution="polar", wavelength=633, D=5, enabled=True
    ):
        WBPart.__init__(self, obj, "RaysPar", enabled)

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
        obj.addProperty("App::PropertyLength", "D", "Shape", "Ray Source Diameter")
        # obj.addProperty("App::PropertyVector","axis","","Direction of propagation")

        obj.nr = nr
        obj.na = na
        obj.distribution = distribution.lower()
        obj.wl = Units.Quantity(
            "{} nm".format(wavelength)
        )  # wavelength is received in nm
        obj.D = D
        obj.Enabled = enabled
        r, g, b = wavelength2RGB(obj.wl.getValueAs("µm").Value)

        obj.ViewObject.ShapeColor = (r, g, b, 0.0)

    def onChanged(self, obj, prop):
        super().onChanged(obj, prop)

        if prop == "wl":
            r, g, b = wavelength2RGB(obj.wl.getValueAs("µm").Value)
            obj.ViewObject.ShapeColor = (r, g, b, 0.0)

    def pyoptools_repr(self, obj):
        pla = obj.getGlobalPlacement()

        X, Y, Z = pla.Base
        RZ, RY, RX = pla.Rotation.toEuler()
        dist = obj.distribution
        nr = obj.nr
        na = obj.na
        wl = obj.wl.getValueAs("µm").Value
        R = obj.D / 2.0
        r = []
        
        label = obj.Label
        
        if obj.Enabled:
            if dist == "polar":
                r = rs_lib.parallel_beam_p(
                    origin=(X, Y, Z),
                    direction=(radians(RX), radians(RY), radians(RZ)),
                    radius=R,
                    num_rays=(nr, na),
                    wavelength=wl,
                    label=label,
                )
            elif dist == "cartesian":
                print("cartesian ray distribution, not implemented yet")
            elif dist == "random":
                print("random ray distribution, not implemented yet")
            else:
                print("Warning ray distribution {} not recognized".format(dist))
        return r

    def execute(self, obj):
        import Part, FreeCAD

        dist = obj.distribution.lower()

        if dist not in ["polar", "cartesian"]:
            obj.distribution = "polar"
            print("Ray Distribution not understood, changing it to polar")

        if dist == "polar":
            r = obj.D.Value / 2.0
            d = Part.makeCylinder(r, 5)
            # d.translate(FreeCAD.Base.Vector(0,0,-0.5))
        else:  # Cartesian
            # Todo: Crear una piramide en lugar de un cono
            d = Part.makeCone(0, 10, 10, dir)
            d.translate(FreeCAD.Base.Vector(0, 0, -0.5))
        obj.Shape = d


def InsertRPar(
    nr=6, na=6, distribution="polar", wavelength=633, D=5, ID="S", enabled=True
):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    RaysParPart(myObj, nr, na, distribution, wavelength, D, enabled)
    myObj.ViewObject.Proxy = 0  # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj
