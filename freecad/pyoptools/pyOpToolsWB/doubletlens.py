# -*- coding: utf-8 -*-
"""Classes used to define a Doublet Lens."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import (
    placementWidget,
)
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget
import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from .sphericallens import buildlens
from math import radians
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getMaterial

class DoubletLensGUI(WBCommandGUI):
    def __init__(self):

        pw = placementWidget()
        mw1 = materialWidget()
        mw2 = materialWidget()

        mw1.ui.label.setText("Material Lens 1")
        mw2.ui.label.setText("Material Lens 2")

        WBCommandGUI.__init__(
            self, [pw, {"mat1": mw1, "mat2": mw2}, "DoubletLens.ui"]
        )

        self.form.ILD.valueChanged.connect(self.ILDChange)
        self.form.CS2_1.valueChanged.connect(self.CS2_1Change)

    def ILDChange(self, *args):
        d = args[0]
        if d == 0.0:
            self.form.CS1_2.setValue(self.form.CS2_1.value())
            self.form.CS1_2.setEnabled(False)
        else:
            self.form.CS1_2.setEnabled(True)

    def CS2_1Change(self, *args):
        d = args[0]
        if not self.form.CS1_2.isEnabled():
            self.form.CS1_2.setValue(d)

    def accept(self):

        CS1_1 = self.form.CS1_1.value()
        CS1_2 = self.form.CS1_2.value()
        CS2_1 = self.form.CS2_1.value()
        CS2_2 = self.form.CS2_2.value()
        CT_1 = self.form.CT1.value()
        CT_2 = self.form.CT2.value()

        D = self.form.D.value()
        ILD = self.form.ILD.value()

        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()

        matcat1 = self.form.mat1.Catalog.currentText()
        if matcat1 == "Value":
            matref1 = str(self.form.mat1.Value.value())
        else:
            matref1 = self.form.mat1.Reference.currentText()

        matcat2 = self.form.mat2.Catalog.currentText()
        if matcat2 == "Value":
            matref2 = str(self.form.mat2.Value.value())
        else:
            matref2 = self.form.mat2.Reference.currentText()

        obj = InsertDL(
            CS1_1,
            CS2_1,
            CT_1,
            CS1_2,
            CS2_2,
            CT_2,
            D,
            ILD,
            "L",
            matcat1,
            matref1,
            matcat2,
            matref2,
        )

        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1

        FreeCADGui.Control.closeDialog()


class DoubletLensMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, DoubletLensGUI)

    def GetResources(self):
        return {
            "MenuText": "Doublet Lens",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Doublet Lens",
            "Pixmap": "",
        }


class DoubletLensPart(WBPart):
    def __init__(
        self,
        obj,
        CS1_1,
        CS2_1,
        CT_1,
        CS1_2,
        CS2_2,
        CT_2,
        D,
        ILD,
        matcat1,
        matref1,
        matcat2,
        matref2,
    ):

        WBPart.__init__(self, obj, "DoubletLens")
        obj.Proxy = self

        obj.addProperty(
            "App::PropertyPrecision",
            "CS1_1",
            "Shape lens 1",
            "Curvature surface 1",
        ).CS1_1 = (0, -10, 10, 1e-3)
        obj.addProperty(
            "App::PropertyPrecision",
            "CS2_1",
            "Shape lens 1",
            "Curvature surface 2",
        ).CS2_1 = (0, -10, 10, 1e-3)

        obj.addProperty(
            "App::PropertyLength",
            "Thk_1",
            "Shape lens 1",
            "Lens 1 center thickness",
        )

        obj.addProperty(
            "App::PropertyPrecision",
            "CS1_2",
            "Shape lens 2",
            "Curvature surface 1",
        ).CS1_2 = (0, -10, 10, 1e-3)
        obj.addProperty(
            "App::PropertyPrecision",
            "CS2_2",
            "Shape lens 2",
            "Curvature surface 2",
        ).CS2_2 = (0, -10, 10, 1e-3)

        obj.addProperty(
            "App::PropertyLength",
            "Thk_2",
            "Shape lens 2",
            "Lens 2 center thickness",
        )

        obj.addProperty("App::PropertyLength", "D", "Global", "Diameter")
        obj.addProperty(
            "App::PropertyLength", "ILD", "Global", "Interlens distance"
        )

        obj.addProperty(
            "App::PropertyString",
            "matcat1",
            "Material lens 1",
            "Material catalog",
        )
        obj.addProperty(
            "App::PropertyString",
            "matref1",
            "Material lens 1",
            "Material reference",
        )

        obj.addProperty(
            "App::PropertyString",
            "matcat2",
            "Material lens 2",
            "Material catalog",
        )
        obj.addProperty(
            "App::PropertyString",
            "matref2",
            "Material lens 2",
            "Material reference",
        )

        obj.CS1_1 = CS1_1
        obj.CS2_1 = CS2_1
        obj.Thk_1 = CT_1

        obj.CS1_2 = CS1_2
        obj.CS2_2 = CS2_2
        obj.Thk_2 = CT_2

        obj.D = D
        obj.ILD = ILD

        obj.matcat1 = matcat1
        obj.matref1 = matref1

        obj.matcat2 = matcat2
        obj.matref2 = matref2

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0, 0.0)

    def pyoptools_repr(self, obj):

        material1 = getMaterial(obj.matcat1, obj.matref1)
        material2 = getMaterial(obj.matcat2, obj.matref2)

        if obj.ILD.Value == 0:
            radius = obj.D.Value / 2.0
            curv_s1 = obj.CS1_1
            curv_s2 = obj.CS2_1
            curv_s3 = obj.CS2_2
            th1 = obj.Thk_1.Value
            th2 = obj.Thk_2.Value
            db = comp_lib.Doublet(
                radius,
                curv_s1,
                curv_s2,
                curv_s3,
                th1,
                th2,
                material1,
                material2,
            )
        else:
            radius = obj.D.Value / 2.0
            curv_s1 = obj.CS1_1
            curv_s2 = obj.CS2_1
            curv_s3 = obj.CS1_2
            curv_s4 = obj.CS2_2

            th1 = obj.Thk_1.Value
            th2 = obj.Thk_2.Value

            ag = obj.ILD.Value
            db = comp_lib.AirSpacedDoublet(
                radius,
                curv_s1,
                curv_s2,
                curv_s3,
                curv_s4,
                th1,
                ag,
                th2,
                material1,
                material2,
            )

        return db

    def execute(self, obj):

        # Todo: Verificat las restricciones por construccion cuando se cambian
        # los parametros a mano

        L1 = buildlens(obj.CS1_1, obj.CS2_1, obj.D.Value, obj.Thk_1.Value)
        L2 = buildlens(obj.CS1_2, obj.CS2_2, obj.D.Value, obj.Thk_2.Value)
        TT = obj.Thk_1.Value + obj.Thk_2.Value + obj.ILD.Value
        L1.translate(
            FreeCAD.Base.Vector(0, 0, -TT / 2.0 + obj.Thk_1.Value / 2.0)
        )
        L2.translate(
            FreeCAD.Base.Vector(0, 0, TT / 2.0 - obj.Thk_2.Value / 2.0)
        )
        obj.Shape = L1.fuse(L2)

    def onDocumentRestored(self, obj):
        """Method to migrate to newer objects type.

        Used for the moment to solve some problems when reopening the files
        https://forum.freecadweb.org/viewtopic.php?f=22&t=60174

        Idea taken from:
        https://wiki.freecadweb.org/Scripted_objects_migration
        """

        super().onDocumentRestored(obj)

        FreeCAD.Console.PrintWarning(
            "Reconfiguring PropertyPrecision in doubletlens"
        )
        # When opening old files, the App::PropertyPrecision used in the
        # curvature properties stop receiving negative numbers. To temporary
        # solve this issue, the properties are re defines (ugly hack)
        CS1_1 = obj.CS1_1
        CS2_1 = obj.CS2_1
        CS1_2 = obj.CS1_2
        CS2_2 = obj.CS2_2
        obj.CS1_1 = (CS1_1, -10, 10, 1e-3)
        obj.CS2_1 = (CS2_1, -10, 10, 1e-3)
        obj.CS1_2 = (CS1_2, -10, 10, 1e-3)
        obj.CS2_2 = (CS2_2, -10, 10, 1e-3)


def InsertDL(
    CS1_1,
    CS2_1,
    CT_1,
    CS1_2,
    CS2_2,
    CT_2,
    D,
    ILD,
    ID,
    matcat1,
    matref1,
    matcat2,
    matref2,
):

    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    DoubletLensPart(
        myObj,
        CS1_1,
        CS2_1,
        CT_1,
        CS1_2,
        CS2_2,
        CT_2,
        D,
        ILD,
        matcat1,
        matref1,
        matcat2,
        matref2,
    )
    myObj.ViewObject.Proxy = (
        0  # this is mandatory unless we code the ViewProvider too
    )
    FreeCAD.ActiveDocument.recompute()
    return myObj
