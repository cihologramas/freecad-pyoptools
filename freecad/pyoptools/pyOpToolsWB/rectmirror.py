# -*- coding: utf-8 -*-
"""Classes used to define a rectangular mirror."""

import FreeCAD
import FreeCADGui
import Part
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getMaterial

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians
_wrn = FreeCAD.Console.PrintWarning


class RectMirrorGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()
        super.__init__([pw, mw, "RectMirror.ui"])

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

        obj = InsertRectM(Ref, Th, SX, SY, ID="M1", matcat=matcat, matref=matref)
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class RectMirrorMenu(WBCommandMenu):
    def __init__(self):
        super().__init__(RectMirrorGUI)

    def GetResources(self):
        return {
            "MenuText": "Rectangular Mirror",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Rectangular Mirror",
            "Pixmap": "",
        }


class RectMirrorPart(WBPart):
    def __init__(self, obj, Ref=100, Th=10, SX=50, SY=50, matcat="", matref=""):
        """RectMirrorPart class.

        Handles the creation and management of rectangular mirror components within the FreeCAD pyOpTools workbench.

        This class defines properties and methods associated with rectangular mirror components, ensuring that they can be
        integrated into the FreeCAD environment with appropriate characteristics and behaviors.

        Properties:
        -----------

        Reflectivity : float
            Reflectivity percentage of the mirror's coating.
        FilterType : list of str
            Type of filter applied to the mirror's coating, with options "NoFilter", "ShortPass", "LongPass", and "BandPass".
        Thk : float
            The thickness of the mirror.
        D : float
            The diameter of the mirror.
        matcat : str
            The catalog of the material used.
        matref : str
            Reference to the specific material.

        Version History:
        --------------
        Version 1:
            - Added FilterType property.
        Version 0:
            - Initial version with basic properties and functionalities.
        """

        super().__init__(obj, "RectangularMirror")
        obj.Proxy = self
        obj.addProperty(
            "App::PropertyPercent",
            "Reflectivity",
            "Coating",
            "Mirror reflectivity",
        )

        obj.addProperty(
            "App::PropertyEnumeration", "FilterType", "Coating", "Coating Filter Type"
        )
        obj.FilterType = ["NoFilter", "ShortPass", "LongPass", "BandPass"]
        obj.FilterType = "NoFilter"

        obj.addProperty("App::PropertyLength", "Thk", "Shape", "Mirror Thickness")
        obj.addProperty("App::PropertyLength", "Width", "Shape", "Mirror width")
        obj.addProperty("App::PropertyLength", "Height", "Shape", "Mirror height")
        obj.addProperty("App::PropertyString", "matcat", "Material", "Material catalog")
        obj.addProperty(
            "App::PropertyString", "matref", "Material", "Material reference"
        )
        obj.Reflectivity = int(Ref)
        obj.Thk = Th
        obj.Width = SX
        obj.Height = SY
        obj.matcat = matcat
        obj.matref = matref

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5, 0.0)

        # Set current RoundMirror Version
        obj.ObjectVersion = 1

    def onChanged(self, obj, prop):
        super().onChanged(obj, prop)

        if prop == "FilterType":
            # Save current cutoff wavelength values
            tmpcutoffs = [0, 0]

            # Remove existing wavelength properties and store their values
            if hasattr(obj, "CutoffWavelength"):
                tmpcutoffs[0] = obj.CutoffWavelength
                tmpcutoffs[1] = tmpcutoffs[0]
                obj.removeProperty("CutoffWavelength")
            elif hasattr(obj, "LowerCutoffWavelength") and hasattr(
                obj, "UpperCutoffWavelength"
            ):
                tmpcutoffs[0] = obj.LowerCutoffWavelength
                tmpcutoffs[1] = obj.UpperCutoffWavelength
                obj.removeProperty("LowerCutoffWavelength")
                obj.removeProperty("UpperCutoffWavelength")

            # Add relevant wavelength properties based on the selected filter type
            if obj.FilterType == "ShortPass" or obj.FilterType == "LongPass":
                obj.addProperty(
                    "App::PropertyLength",
                    "CutoffWavelength",
                    "Coating",
                    "Coating cutoff wavelength",
                )
                obj.CutoffWavelength = tmpcutoffs[0]

            elif obj.FilterType == "BandPass":
                obj.addProperty(
                    "App::PropertyLength",
                    "LowerCutoffWavelength",
                    "Coating",
                    "Coating cutoff wavelength",
                )
                obj.LowerCutoffWavelength = tmpcutoffs[0]
                obj.addProperty(
                    "App::PropertyLength",
                    "UpperCutoffWavelength",
                    "Coating",
                    "Coating cutoff wavelength",
                )
                obj.UpperCutoffWavelength = tmpcutoffs[1]

    def onDocumentRestored(self, obj):
        """
        Handles the migration of objects when a document is restored.

        This method ensures that objects are properly migrated during the document restore process.

        :param obj: The specific FreeCAD object that is being restored.
        """

        super().onDocumentRestored(obj)

        # Verify what migration must be applied, make sure to use if and not elif to assure
        # all the migrations are executed sequentially.

        if obj.ObjectVersion == 0:
            migrate_to_v1(obj)


    def pyoptools_repr(self, obj):
        material = getMaterial(obj.matcat, obj.matref)

        rm = comp_lib.RectMirror(
            (obj.Width.Value, obj.Height.Value, obj.Thk.Value),
            obj.Reflectivity / 100.0,
            material=material,
        )
        return rm

    def execute(self, obj):
        d = Part.makeBox(
            obj.Width.Value,
            obj.Height.Value,
            obj.Thk.Value,
            FreeCAD.Base.Vector(-obj.Width.Value / 2.0, -obj.Height.Value / 2.0, 0),
        )
        obj.Shape = d


def InsertRectM(Ref=100, Th=10, SX=50, SY=50, ID="L", matcat="", matref=""):
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    RectMirrorPart(myObj, Ref, Th, SX, SY, matcat, matref)
    myObj.ViewObject.Proxy = 0  # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj

def migrate_to_v1(obj):
    # Add the FilterType property
    obj.addProperty(
        "App::PropertyEnumeration", "FilterType", "Coating", "Coating Filter Type"
    )
    obj.FilterType = ["NoFilter", "ShortPass", "LongPass", "BandPass"]
    obj.FilterType = "NoFilter"

    # Update to object version  = 1
    obj.ObjectVersion = 1

    _wrn("Migrating rectangular mirror from v0 to v1\n")
