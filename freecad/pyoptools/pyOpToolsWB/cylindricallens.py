# -*- coding: utf-8 -*-
"""Classes used to define a cylindrical lens."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import (
    placementWidget,
)
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget
from .feedback import FeedbackHelper
import Part
import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getMaterial

class CylindricalLensGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()
        WBCommandGUI.__init__(self, [pw, mw, "CylindricalLens.ui"])

    @FeedbackHelper.with_error_handling("Cylindrical Lens")
    def accept(self):
        CS1 = self.form.CS1.value()
        CS2 = self.form.CS2.value()
        CT = self.form.CT.value()
        W = self.form.W.value()
        H = self.form.H.value()
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

        obj = InsertCL(
            CS1, CS2, CT, W, H, ID="L", matcat=matcat, matref=matref
        )
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1


class CylindricalLensMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, CylindricalLensGUI)

    def GetResources(self):
        return {
            "MenuText": "Cylindrical Lens",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Cylindrical Lens",
            "Pixmap": "",
        }


class CylindricalLensPart(WBPart):
    def __init__(
        self, obj, CS1=0.01, CS2=-0.01, CT=10, W=20, H=20, matcat="", matref=""
    ):
        WBPart.__init__(self, obj, "CylindricalLens")

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
        obj.addProperty("App::PropertyLength", "H", "Shape", "Lens height")
        obj.addProperty("App::PropertyLength", "W", "Shape", "Lens width")
        obj.addProperty(
            "App::PropertyString", "matcat", "Material", "Material catalog"
        )
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.CS1 = CS1
        obj.CS2 = CS2
        obj.Thk = CT
        obj.H = H
        obj.W = W
        obj.matcat = matcat
        obj.matref = matref
        obj.ViewObject.Transparency = 50

        obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0, 0.0)

    def execute(self, obj):

        obj.Shape = buildcylens(
            obj.CS1, obj.CS2, obj.W.Value, obj.H.Value, obj.Thk.Value
        )

    def pyoptools_repr(self, obj):
        thickness = obj.Thk.Value
        h = obj.H.Value
        w = obj.W.Value
        curvature_s1 = obj.CS1
        curvature_s2 = obj.CS2

        material = getMaterial(obj.matcat, obj.matref)

        return comp_lib.CylindricalLens(
            size=(h, w),
            thickness=thickness,
            curvature_s1=curvature_s1,
            curvature_s2=curvature_s2,
            material=material,
        )

    def onDocumentRestored(self, obj):
        """Method to migrate to newer objects type.

        Used for the moment to solve some problems when reopening the files
        https://forum.freecadweb.org/viewtopic.php?f=22&t=60174

        Idea taken from:
        https://wiki.freecadweb.org/Scripted_objects_migration
        """
        
        super().onDocumentRestored(obj)
        
        FreeCAD.Console.PrintWarning(
            "Reconfiguring PropertyPrecision in cylindricallens"
        )
        # When opening old files, the App::PropertyPrecision used in the
        # curvature properties stop receiving negative numbers. To temporary
        # solve this issue, the properties are re defines (ugly hack)
        CS1 = obj.CS1
        obj.CS1 = (CS1, -10, 10, 1e-3)
        CS2 = obj.CS2
        obj.CS2 = (CS2, -10, 10, 1e-3)


def InsertCL(
    CS1=0.01, CS2=-0.01, CT=10, W=20, H=20, ID="L", matcat="", matref=""
):

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    CylindricalLensPart(myObj, CS1, CS2, CT, W, H, matcat, matref)
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj


def buildcylens(CS1, CS2, W, H, CT):

    d = Part.makeBox(H, W, CT + H)
    d.translate(FreeCAD.Base.Vector(-H / 2.0, -W / 2, -(CT + H) / 2))

    if CS1 == 0:
        R1 = 1e6
    else:
        R1 = 1.0 / CS1

    f1 = Part.makeCylinder(
        abs(R1),
        W,
        FreeCAD.Base.Vector(0, -W / 2, 0),
        FreeCAD.Base.Vector(0, 1, 0),
    )
    f1.translate(FreeCAD.Base.Vector(0, 0, R1 - CT / 2))

    if CS2 == 0:
        R2 = 1e6
    else:
        R2 = 1.0 / CS2

    f2 = Part.makeCylinder(
        abs(R2),
        W,
        FreeCAD.Base.Vector(0, -W / 2, 0),
        FreeCAD.Base.Vector(0, 1, 0),
    )
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
