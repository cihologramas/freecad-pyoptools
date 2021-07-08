# -*- coding: utf-8 -*-
"""Classes used to define a powell lens."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget

import Part

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians
from math import sqrt


class PowellLensGUI(WBCommandGUI):
    def __init__(self):

        pw = placementWidget()
        mw = materialWidget()
        WBCommandGUI.__init__(self, [pw, mw, "PowellLens.ui"])

    def accept(self):
        R = self.form.R.value()
        K = self.form.K.value()
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

        obj = InsertSL(R, CT, K, D, ID="PL", matcat=matcat, matref=matref)
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class PowellLensMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, PowellLensGUI)

    def GetResources(self):
        return {
            "MenuText": "Powell Lens",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Powell Lens",
            "Pixmap": "",
        }


class PowellLensPart(WBPart):
    def __init__(
        self, obj, R=3.00, CT=7.62, K=-4.302, D=8.89, matcat="", matref=""
    ):
        WBPart.__init__(self, obj, "PowellLens")

        # Todo: Mirar como se puede usar un quantity
        obj.addProperty(
            "App::PropertyPrecision",
            "R",
            "Shape",
            "Curvature Radius Aspherical Surface ",
        ).R = (0, -10, 10, 1e-3)
        obj.addProperty(
            "App::PropertyPrecision", "K", "Shape", "Powell Lens Conicity "
        ).K = (0, -10, 10, 1e-3)
        obj.addProperty(
            "App::PropertyLength",
            "CT",
            "Shape",
            "Powell Lens Center Thickness",
        )
        obj.addProperty(
            "App::PropertyLength", "D", "Shape", "Powell Lens Diameter"
        )
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.R = R
        obj.K = K
        obj.CT = CT
        obj.D = D
        obj.matcat = matcat
        obj.matref = matref
        obj.ViewObject.Transparency = 50

        obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0, 0.0)

    def execute(self, obj):
        obj.Shape = buildlens(obj.R, obj.CT.Value, obj.K, obj.D.Value)

    def pyoptools_repr(self, obj):
        radius = obj.D.Value / 2.0
        thickness = obj.CT.Value
        curvature = obj.R
        K = obj.K
        matcat = obj.matcat
        matref = obj.matref
        if matcat == "Value":
            # Esto es para poder imprimir en la consola de FreeCAD
            # FreeCAD.Console.PrintMessage(str(obj.matref) + "\n")
            material = float(matref.replace(",", "."))
            # FreeCAD.Console.PrintMessage(str(material) + "\n")
        else:
            material = getattr(matlib.material, matcat)[matref]

        return comp_lib.PowellLens(
            radius=radius,
            thickness=thickness,
            K=K,
            R=curvature,
            material=material,
        )


def InsertSL(R=3.00, CT=7.62, K=-4.302, D=8.89, ID="PL", matcat="", matref=""):
    import FreeCAD

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    PowellLensPart(myObj, R, CT, K, D, matcat, matref)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj


def buildlens(R, CT, K, D):

    y = -500
    Nb = 10
    Step = 1000 / Nb
    x = 0
    xi = x
    yi = y
    zi = R * yi ** 2 / (1 + sqrt(1 - (1 + K) * yi ** 2 * R ** 2))
    for I in range(Nb):
        yy = y + Step
        z = R * y ** 2 / (1 + sqrt(1 - (1 + K) * y ** 2 * R ** 2))
        zz = R * yy ** 2 / (1 + sqrt(1 - (1 + K) * yy ** 2 * R ** 2))

        if I == 0:
            line = Part.makeLine((x, y, z), (x, yy, zz))
            t = Part.Wire([line])
        else:
            line = Part.makeLine((x, y, z), (x, yy, zz))
            t = Part.Wire([t, line])
        y = yy
    xf = xi
    yf = y
    zf = zz

    nomme = Part.makeLine((xi, yi, zi), (xf, yf, zf))
    t = Part.Wire([t, nomme])

    t = Part.Face(t)
    e = t.extrude(FreeCAD.Base.Vector(D, 0, 0))
    e.translate(FreeCAD.Base.Vector(-D / 2.0, 0, 0))

    d = Part.makeCylinder(D / 2.0, CT)

    t = d.common(e)

    return t
