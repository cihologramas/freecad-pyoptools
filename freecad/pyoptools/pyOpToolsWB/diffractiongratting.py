# -*- coding: utf-8 -*-
"""Classes used to define a diffraction gratting."""
import FreeCAD
import FreeCADGui
import Part

from .feedback import FeedbackHelper
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getMaterial

class DiffractionGrattingGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()
        WBCommandGUI.__init__(self, [pw, mw, "DiffractionGratting.ui"])

    @FeedbackHelper.with_error_handling("Diffraction Grating")
    def accept(self):
        Th = self.form.Thickness.value()
        Ref = self.form.Reflectivity.value()
        SX = self.form.SX.value()
        SY = self.form.SY.value()
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

        Ang = self.form.Angle.value()
        GP = self.form.Gp.value()
        M = []
        if self.form.O3n.isChecked():
            M.append(-3)
        if self.form.O2n.isChecked():
            M.append(-2)
        if self.form.O1n.isChecked():
            M.append(-1)
        if self.form.O0.isChecked():
            M.append(0)
        if self.form.O1.isChecked():
            M.append(1)
        if self.form.O2.isChecked():
            M.append(2)
        if self.form.O3.isChecked():
            M.append(3)

        obj = InsertDiffG(
            Ref, Th, SX, SY, Ang, GP, M, ID="G1", matcat=matcat, matref=matref
        )
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1


class DiffractionGrattingMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, DiffractionGrattingGUI)

    def GetResources(self):
        return {"MenuText": "Diffraction Gratting",
                #"Accel": "Ctrl+M",
                "ToolTip": "Add Diffraction Gratting",
                "Pixmap": ""}

class DiffractionGrattingPart(WBPart):
    def __init__(
        self,
        obj,
        Ref=100,
        Th=10,
        SX=50,
        SY=50,
        Ang=0.0,
        Gp=1000.0,
        M=[1],
        matcat="",
        matref="",
    ):

        WBPart.__init__(self, obj, "RectangularMirror")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyPercent",
            "Reflectivity",
            "Coating",
            "Mirror reflectivity",
        )
        obj.addProperty(
            "App::PropertyLength", "Thk", "Shape", "Mirror Thickness"
        )
        obj.addProperty(
            "App::PropertyLength", "Width", "Shape", "Mirror width"
        )
        obj.addProperty(
            "App::PropertyLength", "Height", "Shape", "Mirror height"
        )
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.addProperty(
            "App::PropertyLength", "GP", "Shape", "Gratting period"
        )
        obj.addProperty(
            "App::PropertyAngle", "Ang", "Shape", "Gratting Orientation"
        )
        obj.addProperty(
            "App::PropertyIntegerList", "M", "Shape", "Orders to show"
        )
        obj.Reflectivity = int(Ref)
        obj.Thk = Th
        obj.Width = SX
        obj.Height = SY
        obj.matcat = matcat
        obj.matref = matref
        obj.M = M

        obj.GP = FreeCAD.Units.Quantity(
            "{} nm".format(Gp)
        )  # The gratting period is passed in nm
        obj.Ang = Ang

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (0.0, 1.0, 0.0, 0.0)

    def pyoptools_repr(self, obj):
        
        material = getMaterial(obj.matcat, obj.matref)

        lpmm = 1.0 / obj.GP.getValueAs("mm").Value
        rm = comp_lib.RectGratting(
            (obj.Width.Value, obj.Height.Value, obj.Thk.Value),
            obj.Reflectivity / 100.0,
            lpmm=lpmm,
            angle=obj.Ang.getValueAs("rad").Value,
            material=material,
            M=obj.M,
        )
        return rm

    def execute(self, obj):

        d = Part.makeBox(
            obj.Width.Value,
            obj.Height.Value,
            obj.Thk.Value,
            FreeCAD.Base.Vector(
                -obj.Width.Value / 2.0, -obj.Height.Value / 2.0, 0
            ),
        )
        obj.Shape = d
        print(obj.M)


def InsertDiffG(
    Ref=100,
    Th=10,
    SX=50,
    SY=50,
    Ang=0,
    GP=1000.0,
    M=[1],
    ID="L",
    matcat="",
    matref="",
):
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    DiffractionGrattingPart(myObj, Ref, Th, SX, SY, Ang, GP, M, matcat, matref)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj
