# -*- coding: utf-8 -*-
"""Classes used to define a Spherical lens."""
import FreeCAD
import FreeCADGui
import Part

from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget


import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians


class SphericalLensGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()

        WBCommandGUI.__init__(self, [pw, mw, "SphericalLens.ui"])

    def accept(self):
        CS1 = self.form.CS1.value()
        CS2 = self.form.CS2.value()
        CT = self.form.CT.value()
        D = self.form.D.value()
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

        obj = InsertSL(CS1, CS2, CT, D, ID="L", matcat=matcat, matref=matref)
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class SphericalLensMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, SphericalLensGUI)

    def GetResources(self):
        return {
            "MenuText": "Spherical Lens",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Spherical Lens",
            "Pixmap": "",
        }


class SphericalLensPart(WBPart):
    def __init__(
        self, obj, CS1=0.01, CS2=-0.01, CT=10, D=50, matcat="", matref=""
    ):
        WBPart.__init__(self, obj, "SphericalLens")

        # Todo: Mirar como se puede usar un quantity
        obj.addProperty(
            "App::PropertyPrecision", "CS1", "Shape", "Curvature surface 1"
        ).CS1 = (0, -10, 10, 1e-3)
        obj.addProperty(
            "App::PropertyPrecision", "CS2", "Shape", "Curvature surface 2"
        ).CS2 = (0, -10, 10, 1e-3)

        obj.addProperty(
            "App::PropertyLength", "Thk", "Shape", "Lens center thickness"
        )
        obj.addProperty("App::PropertyLength", "D", "Shape", "Lens diameter")
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.CS1 = CS1
        obj.CS2 = CS2
        obj.Thk = CT
        obj.D = D
        obj.matcat = matcat
        obj.matref = matref
        obj.ViewObject.Transparency = 50

        obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0, 0.0)

    def execute(self, obj):

        obj.Shape = buildlens(obj.CS1, obj.CS2, obj.D.Value, obj.Thk.Value)

    def pyoptools_repr(self, obj):
        radius = obj.D.Value / 2.0
        thickness = obj.Thk.Value
        curvature_s1 = obj.CS1
        curvature_s2 = obj.CS2
        matcat = obj.matcat
        matref = obj.matref
        if matcat == "Value":
            material = float(matref.replace(",", "."))
        else:
            material = getattr(matlib.material, matcat)[matref]

        return comp_lib.SphericalLens(
            radius=radius,
            thickness=thickness,
            curvature_s1=curvature_s1,
            curvature_s2=curvature_s2,
            material=material,
        )


def InsertSL(CS1=0.01, CS2=-0.01, CT=10, D=50, ID="L", matcat="", matref=""):

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    SphericalLensPart(myObj, CS1, CS2, CT, D, matcat, matref)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj


def buildlens(CS1, CS2, D, CT):

    d = Part.makeCylinder(D / 2.0, CT + D)
    d.translate(FreeCAD.Base.Vector(0, 0, -(CT + D) / 2))

    if CS1 == 0:
        R1 = 1e6
    else:
        R1 = 1.0 / CS1
    f1 = Part.makeSphere(abs(R1))
    f1.translate(FreeCAD.Base.Vector(0, 0, R1 - CT / 2))

    if CS2 == 0:
        R2 = 1e6
    else:
        R2 = 1.0 / CS2
    f2 = Part.makeSphere(abs(R2))
    f2.translate(FreeCAD.Base.Vector(0, 0, R2 + CT / 2))

    if R1 > 0:
        t = d.common(f1)
    else:
        t = d.cut(f1)
    if R2 > 0:
        t = t.cut(f2)
    else:
        t = t.common(f2)

    return t
