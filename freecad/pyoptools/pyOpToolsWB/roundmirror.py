# -*- coding: utf-8 -*-
"""Classes used to define a round mirror."""
import FreeCAD
import FreeCADGui
import Part
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians


class RoundMirrorGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()
        WBCommandGUI.__init__(self, [pw, mw, "RoundMirror.ui"])

    def accept(self):
        Th = self.form.Thickness.value()
        Ref = self.form.Reflectivity.value()
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

        obj = InsertRM(Ref, Th, D, ID="M1", matcat=matcat, matref=matref)
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class RoundMirrorMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, RoundMirrorGUI)

    def GetResources(self):
        return {
            "MenuText": "Round Mirror",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Round Mirror",
            "Pixmap": "",
        }


class RoundMirrorPart(WBPart):
    def __init__(self, obj, Ref=100, Th=10, D=50, matcat="", matref=""):

        WBPart.__init__(self, obj, "RoundMirror")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyPercent",
            "Reflectivity",
            "Coating",
            "Mirror reflectivity",
        )
        obj.addProperty(
            "App::PropertyLength", "Thk", "Shape", "Mirror thickness"
        )
        obj.addProperty("App::PropertyLength", "D", "Shape", "Mirror diameter")
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.Reflectivity = int(Ref)
        obj.Thk = Th
        obj.D = D
        obj.matcat = matcat
        obj.matref = matref

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5, 0.0)

    def pyoptools_repr(self, obj):
        matcat = obj.matcat
        matref = obj.matref
        if matcat == "Value":
            material = float(matref.replace(",", "."))
        elif matcat == "aliases":
            material = matlib.material[matref]
        else:
            material = getattr(matlib.material, matcat)[matref]
        print(material, type(material))
        rm = comp_lib.RoundMirror(
            obj.D.Value / 2.0,
            obj.Thk.Value,
            obj.Reflectivity / 100.0,
            material=material,
        )
        return rm

    def execute(self, obj):

        d = Part.makeCylinder(
            obj.D.Value / 2.0, obj.Thk.Value, FreeCAD.Base.Vector(0, 0, 0)
        )
        # Esto aca no funciona
        # d.translate(FreeCAD.Base.Vector(0,0,-obj.Thickness))

        obj.Shape = d


def InsertRM(Ref=100, Th=10, D=50, ID="L", matcat="", matref=""):

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    RoundMirrorPart(myObj, Ref, Th, D, matcat, matref)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj
