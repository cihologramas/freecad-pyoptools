# -*- coding: utf-8 -*-
"""Classes used to define a single ray."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget

from pyoptools.misc.pmisc.misc import wavelength2RGB
from pyoptools.raytrace.ray import Ray
from math import tan, radians
from FreeCAD import Units
import FreeCAD


class RayGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "Ray.ui"])

    def accept(self):

        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()

        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()
        
        wavelength = self.form.wavelength.value()
        enabled = self.form.Enabled.isChecked()

        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))

        m.move((X, Y, Z))
        
        obj=InsertRay(wavelength, "R", enabled)

        p1 = FreeCAD.Placement(m)
        obj.Placement = p1

        FreeCADGui.Control.closeDialog()


class RayMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, RayGUI)

    def GetResources(self):
        return {
            "MenuText": "Add Ray Source",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Ray Source",
            "Pixmap": "",
        }


class RayPart(WBPart):
    def __init__(self,obj, wavelength=633, enabled=True):
        WBPart.__init__(self,obj,"Ray")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyLength", "wl", "Options", "Wavelength of the source"
        )

        # wavelength is received in nm
        obj.wl = Units.Quantity("{} nm".format(wavelength))
        obj.Enabled = enabled

        r, g, b = wavelength2RGB(obj.wl.getValueAs("µm").Value)
        obj.ViewObject.ShapeColor = (r, g, b, 0.0)

    def propertyChanged(self, obj, prop):

        # To keep all the housekeeping that WBPart do, this method replaces
        # the standard onChanged

        if prop == "wl":
            r, g, b = wavelength2RGB(obj.wl.getValueAs("µm").Value)
            obj.ViewObject.ShapeColor = (r, g, b, 0.0)

    def pyoptools_repr(self, obj):

        wl = obj.wl.getValueAs("µm").Value

        pla = obj.getGlobalPlacement()
        X, Y, Z = pla.Base

        r_vec = pla.Rotation.multVec(FreeCAD.Base.Vector(0, 0, 1))

        return [
            Ray(pos=(X, Y, Z), dir=(r_vec.x, r_vec.y, r_vec.z), wavelength=wl)
        ]

    def execute(self, obj):
        import Part

        d1 = Part.makeCylinder(0.25, 10)
        d2 = Part.makeCone(0.5, 0, 1)
        d2.translate(FreeCAD.Base.Vector(0, 0, 10))

        d = d1.fuse(d2)

        obj.Shape = d


def InsertRay(wavelength=633, ID="R", enabled=True):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    RayPart(myObj, wavelength, enabled)

    # this is mandatory unless we code the ViewProvider too
    myObj.ViewObject.Proxy = 0
    FreeCAD.ActiveDocument.recompute()
    return myObj
