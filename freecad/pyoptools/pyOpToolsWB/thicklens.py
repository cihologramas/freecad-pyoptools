# -*- coding: utf-8 -*-
"""Classes used to define an ideal thick lens."""

import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getMaterial

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from pyoptools.raytrace.system.idealcomponent import IdealThickLens
from pyoptools.raytrace.shape.circular import Circular
from math import radians


class ThickLensGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "IdealThickLens.ui"])

    def accept(self):
        Th = self.form.Thk.value()
        D = self.form.D.value()

        PP1 = self.form.PP1.value()
        PP2 = self.form.PP2.value()

        showpp = self.form.ShowPP.isChecked()
        showft = self.form.ShowFRT.isChecked()
        f = self.form.f.value()

        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()

        PupP = self.form.PupPos.value()
        PupD = self.form.PupD.value()

        PupEn = self.form.RefSurf1.isChecked() or self.form.RefSurf2.isChecked()
        PupRS = self.form.RefSurf1.isChecked()

        obj = InsertTL(
            Th, D, PP1, PP2, f, PupP, PupD, PupEn, PupRS, showpp, showft, ID="L"
        )
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class ThickLensMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, ThickLensGUI)

    def GetResources(self):
        return {
            "MenuText": "Thick Lens",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Ideal Thick Lens",
            "Pixmap": "",
        }


class ThickLensPart(WBPart):
    def __init__(
        self,
        obj,
        Th=10,
        D=50,
        PP1=0,
        PP2=0,
        f=100,
        PupP=0,
        PupD=10,
        PupRS=False,
        PupEn=False,
        SPP=False,
        SFRT=False,
    ):
        WBPart.__init__(self, obj, "ThickLens")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyLength",
            "Thk",
            "Shape",
            "Lens Thickness (distance between entrance and exit surfaces in the lens)",
        )
        obj.addProperty("App::PropertyLength", "D", "Shape", "Lens diameter")
        obj.addProperty(
            "App::PropertyDistance",
            "PP1P",
            "Shape",
            "Principal plane 1 position",
        )
        obj.addProperty(
            "App::PropertyDistance",
            "PP2P",
            "Shape",
            "Principal plane 2 position",
        )
        obj.addProperty("App::PropertyDistance", "PupP", "Shape", "Pupil position")
        obj.addProperty("App::PropertyDistance", "PupD", "Shape", "Pupil diameter")
        obj.addProperty(
            "App::PropertyBool",
            "PupRS",
            "Shape",
            "Use surface 1 as the reference surface, if not selected use surface 2",
        )
        obj.addProperty(
            "App::PropertyBool", "PupEn", "Shape", "Enable pupil simulation"
        )

        obj.addProperty("App::PropertyDistance", "f", "Shape", "lens Focal length")
        obj.addProperty("App::PropertyBool", "SPP", "Other", "Show principal planes")
        obj.addProperty("App::PropertyBool", "SFRT", "Other", "Show full ray trace")
        obj.Thk = Th
        obj.D = D
        obj.PP1P = PP1
        obj.PP2P = PP2
        obj.SPP = SPP
        obj.SFRT = SFRT
        obj.f = f
        obj.PupEn = PupEn
        obj.PupRS = PupRS

        obj.ViewObject.Transparency = 50

        obj.PupP = PupP
        obj.PupD = PupD
        obj.PupEn = PupEn
        obj.PupRS = PupRS

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (1.0, 0.0, 0.0, 0.0)

    def pyoptools_repr(self, obj):
        if not obj.PupEn:
            pupil = None
        else:
            pup_pos = obj.PupP.Value
            pup_shape = Circular(
                radius=obj.PupD.Value / 2.0,
            )
            pup_rs = obj.PupRS
            pupil = pup_pos, pup_shape, pup_rs

        return IdealThickLens(
            Circular(radius=obj.D.Value / 2.0),
            obj.Thk.Value,
            (obj.PP1P.Value, obj.PP2P.Value),
            focal_length=obj.f.Value,
            show_internal_rays=obj.SFRT,
            pupil_config=pupil,
        )

    def execute(self, obj):
        import Part, FreeCAD

        d = Part.makeCylinder(
            obj.D.Value / 2.0,
            obj.Thk.Value,
            FreeCAD.Base.Vector(0, 0, -obj.Thk.Value / 2),
        )
        p1 = Part.makeCylinder(
            obj.D.Value / 2.0,
            0.01,
            FreeCAD.Base.Vector(0, 0, obj.PP1P.Value - obj.Thk.Value / 2),
        )
        p2 = Part.makeCylinder(
            obj.D.Value / 2.0,
            0.01,
            FreeCAD.Base.Vector(0, 0, obj.Thk.Value / 2 + obj.PP2P.Value),
        )

        puppos = (
            obj.PupP.Value - obj.Thk.Value / 2
            if obj.PupRS
            else obj.PupP.Value + obj.Thk.Value / 2
        )
        pup = Part.makeCylinder(
            obj.PupD.Value / 2.0, 0.01, FreeCAD.Base.Vector(0, 0, puppos)
        )

        if obj.SPP:
            oblist = [d, p1, p2]
        else:
            oblist = [d]
        if obj.PupEn:
            oblist = oblist + [pup]

        obj.Shape = Part.makeCompound(oblist)


# (self,obj,Th=10,D=50,PP1=0,PP2=0,f=100,Pup1P=0, Pup1D=10,Pup1En=False,Pup2P=0, Pup2D=10,Pup2En=False, SPP=False,SFRT=False):
def InsertTL(
    Th=10,
    D=50,
    PP1=2,
    PP2=-2,
    f=100,
    PupP=0,
    PupD=10,
    PupRS=True,
    PupEn=False,
    SPP=False,
    SFRT=False,
    ID="L",
):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    ThickLensPart(myObj, Th, D, PP1, PP2, f, PupP, PupD, PupRS, PupEn, SPP, SFRT)
    myObj.ViewObject.Proxy = 0  # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj
