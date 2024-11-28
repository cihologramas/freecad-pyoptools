# -*- coding: utf-8 -*-
"""Classes used to define a Spherical lens."""

import FreeCAD
import FreeCADGui
import Part

from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import (
    placementWidget,
)
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getMaterial

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians

_wrn = FreeCAD.Console.PrintWarning


class SphericalLensGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()

        WBCommandGUI.__init__(self, [pw, mw, "SphericalLens.ui"])

    def accept(self):
        curvature_front = self.form.CurvatureFront.value()
        curvature_back = self.form.CurvatureBack.value()
        center_thickness = self.form.CenterThickness.value()
        diameter = self.form.Diameter.value()
        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()
        material_catalog = self.form.Catalog.currentText()
        if material_catalog == "Value":
            material_reference = str(self.form.Value.value())
        else:
            material_reference = self.form.Reference.currentText()

        obj = InsertSL(
            curvature_front,
            curvature_back,
            center_thickness,
            diameter,
            ID="L",
            matcat=material_catalog,
            matref=material_reference,
        )
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
    """A FreeCAD part for creating spherical optical lenses.

    This class creates and manages spherical lens objects in the pyOpTools workbench.
    It provides properties to define the lens geometry and optical material.

    Properties
    ----------
    CurvatureFront : float
        Curvature of the front surface in 1/mm
    CurvatureBack : float
        Curvature of the back surface in 1/mm
    CenterThickness : PropertyLength
        Thickness of the lens at its optical center (supports units)
    Diameter : PropertyLength
        Diameter of the lens (supports units)
    MaterialCatalog : str
        Name of the optical material catalog
    MaterialReference : str
        Reference code for the lens material in the catalog

    Notes
    -----
    A biconvex lens is created with positive CurvatureFront and negative CurvatureBack.
    A curvature of 0 creates a flat surface.
    """

    def __init__(
        self,
        obj,
        curvature_front=0.01,
        curvature_back=-0.01,
        center_thickness=10,
        diameter=50,
        material_catalog="",
        material_reference="",
    ):
        WBPart.__init__(self, obj, "SphericalLens")

        obj.addProperty(
            "App::PropertyPrecision",
            "CurvatureFront",  # More descriptive than CS1
            "Shape",
            "Curvature of the front surface (1/mm)",
        ).CurvatureFront = (curvature_front, -10, 10, 1e-3)

        obj.addProperty(
            "App::PropertyPrecision",
            "CurvatureBack",  # More descriptive than CS2
            "Shape",
            "Curvature of the back surface (1/mm)",
        ).CurvatureBack = (curvature_back, -10, 10, 1e-3)

        obj.addProperty(
            "App::PropertyLength",
            "CenterThickness",  # More descriptive than Thk
            "Shape",
            "Lens thickness at optical center",
        )

        obj.addProperty(
            "App::PropertyLength",
            "Diameter",  # More descriptive than D
            "Shape",
            "Lens diameter",
        )

        obj.addProperty(
            "App::PropertyString",
            "MaterialCatalog",  # More descriptive than matcat
            "Material",
            "Material catalog name",
        )

        obj.addProperty(
            "App::PropertyString",
            "MaterialReference",  # More descriptive than matref
            "Material",
            "Material reference code",
        )

        obj.CenterThickness = center_thickness
        obj.Diameter = diameter
        obj.MaterialCatalog = material_catalog
        obj.MaterialReference = material_reference
        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0, 0.0)

        obj.ObjectVersion = 1

    def execute(self, obj):
        obj.Shape = buildlens(
            obj.CurvatureFront,
            obj.CurvatureBack,
            obj.Diameter.Value,
            obj.CenterThickness.Value,
        )

    def pyoptools_repr(self, obj):
        radius = obj.Diameter.Value / 2.0
        thickness = obj.CenterThickness.Value
        curvature_s1 = obj.CurvatureFront
        curvature_s2 = obj.CurvatureBack

        material = getMaterial(obj.MaterialCatalog, obj.MaterialReference)

        return comp_lib.SphericalLens(
            radius=radius,
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

        if obj.ObjectVersion == 0:
            migrate_to_v1(obj)

        # App::PropertyPrecision do not save the limits. They must be reset each time the
        # files are opened.
        curvature_front = obj.CurvatureFront
        obj.CurvatureFront = (curvature_front, -10, 10, 1e-3)
        curvature_back = obj.CurvatureBack
        obj.CurvatureBack = (curvature_back, -10, 10, 1e-3)


def InsertSL(CS1=0.01, CS2=-0.01, CT=10, D=50, ID="L", matcat="", matref=""):
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    SphericalLensPart(myObj, CS1, CS2, CT, D, matcat, matref)
    myObj.ViewObject.Proxy = 0  # this is mandatory unless we code the ViewProvider too
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


def migrate_to_v1(obj):
    curvature_front = obj.CS1
    curvature_back = obj.CS2
    center_thickness = obj.Thk
    diameter = obj.D
    material_catalog = obj.matcat
    material_reference = obj.matref

    obj.addProperty(
        "App::PropertyPrecision",
        "CurvatureFront",  # More descriptive than CS1
        "Shape",
        "Curvature of the front surface (1/mm)",
    ).CurvatureFront = (curvature_front, -10, 10, 1e-3)

    obj.addProperty(
        "App::PropertyPrecision",
        "CurvatureBack",  # More descriptive than CS2
        "Shape",
        "Curvature of the back surface (1/mm)",
    ).CurvatureBack = (curvature_back, -10, 10, 1e-3)

    obj.addProperty(
        "App::PropertyLength",
        "CenterThickness",  # More descriptive than Thk
        "Shape",
        "Lens thickness at optical center",
    )

    obj.addProperty(
        "App::PropertyLength",
        "Diameter",  # More descriptive than D
        "Shape",
        "Lens diameter",
    )

    obj.addProperty(
        "App::PropertyString",
        "MaterialCatalog",  # More descriptive than matcat
        "Material",
        "Material catalog name",
    )

    obj.addProperty(
        "App::PropertyString",
        "MaterialReference",  # More descriptive than matref
        "Material",
        "Material reference code",
    )

    obj.CenterThickness = center_thickness
    obj.Diameter = diameter
    obj.MaterialCatalog = material_catalog
    obj.MaterialReference = material_reference
    obj.ViewObject.Transparency = 50

    obj.removeProperty("CS1")
    obj.removeProperty("CS2")
    obj.removeProperty("Thk")
    obj.removeProperty("D")
    obj.removeProperty("matcat")
    obj.removeProperty("matref")

    # Update to object version  = 1
    obj.ObjectVersion = 1

    _wrn("Migrating round mirror from v0 to v1\n")
