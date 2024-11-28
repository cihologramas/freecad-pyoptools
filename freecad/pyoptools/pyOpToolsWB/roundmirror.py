# -*- coding: utf-8 -*-
"""Classes used to define a round mirror."""

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


class RoundMirrorGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()
        super().__init__([pw, mw, "RoundMirror.ui"])

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
        super().__init__(RoundMirrorGUI)

    def GetResources(self):
        return {
            "MenuText": "Round Mirror",
            # "Accel": "Ctrl+M",
            "ToolTip": "Add Round Mirror",
            "Pixmap": "",
        }


class RoundMirrorPart(WBPart):
    """RoundMirrorPart class.

    Handles the creation and management of round mirror components within the FreeCAD pyOpTools workbench.

    This class defines properties and methods associated with round mirror components, ensuring that they can be
    integrated into the FreeCAD environment with appropriate characteristics and behaviors.

    Properties:
    ----------
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
        - The dynamically generated: CutoffWavelength, LowerCutoffWavelength,
          UpperCutoffWavelength where also added.
    Version 0:
        - Initial version with basic properties and functionalities.
    """

    def __init__(self, obj, Ref=100, Th=10, D=50, matcat="", matref=""):
        """
        Initializes a new instance of the RoundMirrorPart class.

        Parameters:
        ----------
        obj : FreeCAD object
            The FreeCAD object instance to which this part belongs.
        Ref : int, optional
            Initial reflectivity of the mirror (default is 100).
        Th : float, optional
            Initial thickness of the mirror (default is 10).
        D : float, optional
            Initial diameter of the mirror (default is 50).
        matcat : str, optional
            Initial material catalog (default is an empty string).
        matref : str, optional
            Initial material reference (default is an empty string).
        """

        super().__init__(obj, "RoundMirror")

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

        obj.addProperty("App::PropertyLength", "Thk", "Shape", "Mirror thickness")
        obj.addProperty("App::PropertyLength", "D", "Shape", "Mirror diameter")
        obj.addProperty("App::PropertyString", "matcat", "Material", "Material catalog")
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
        if obj.FilterType == "NoFilter":
            filter_spec = ("nofilter",)
        elif obj.FilterType == "ShortPass":
            filter_spec = ("shortpass", obj.CutoffWavelength.getValueAs("µm"))
        elif obj.FilterType == "LongPass":
            filter_spec = ("longpass", obj.CutoffWavelength.getValueAs("µm"))
        elif obj.FilterType == "BandPass":
            filter_spec = (
                "bandpass",
                obj.LowerCutoffWavelength.getValueAs("µm"),
                obj.UpperCutoffWavelength.getValueAs("µm"),
            )
        else:
            raise ValueError(f"Unsupported FilterType: {obj.FilterType}")

        material = getMaterial(obj.matcat, obj.matref)
        rm = comp_lib.RoundMirror(
            obj.D.Value / 2.0,
            obj.Thk.Value,
            obj.Reflectivity / 100.0,
            material=material,
            filter_spec=filter_spec,
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

    _wrn("Migrating round mirror from v0 to v1\n")
