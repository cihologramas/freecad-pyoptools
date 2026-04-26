# -*- coding: utf-8 -*-
"""Classes used to define a round mirror."""

import FreeCAD
import FreeCADGui
import Part
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from .feedback import FeedbackHelper
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from freecad.pyoptools.pyOpToolsWB.widgets.materialWidget import materialWidget
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getMaterial

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians, sin

_wrn = FreeCAD.Console.PrintWarning


class RoundMirrorGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        mw = materialWidget()
        super().__init__([pw, mw, "RoundMirror.ui"])

    @FeedbackHelper.with_error_handling("Round Mirror")
    def accept(self):
        Th = self.form.Thickness.value()
        Ref = self.form.Reflectivity.value()
        D = self.form.D.value()
        WA = self.form.WedgeAngle.value()
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

        obj = InsertRM(Ref, Th, D, ID="M1", matcat=matcat, matref=matref, WedgeAngle=WA)
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1


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

    def __init__(self, obj, Ref=100, Th=10, D=50, matcat="", matref="", WedgeAngle=0.0):
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
        WedgeAngle : float, optional
            Tilt angle (degrees) of S2 around the Y-axis. Default is 0
            (parallel faces, no wedge). The ``thickness`` value always
            represents the center thickness.
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

        obj.addProperty(
        "App::PropertyAngle", "WedgeAngle", "Shape", "Wedge angle"
        )

        obj.WedgeAngle = WedgeAngle

        # Set current RoundMirror Version
        obj.ObjectVersion = 2

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
        if obj.ObjectVersion == 1:
            migrate_to_v2(obj)

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
            wedge_angle=radians(obj.WedgeAngle),
        )
        return rm

    def execute(self, obj):
        R = obj.D.Value / 2.0
        Thk = obj.Thk.Value
        wa = obj.WedgeAngle.Value

        # WedgeAngle == 0: plain cylinder, identical to original behavior
        if wa == 0:
            obj.Shape = Part.makeCylinder(R, Thk, FreeCAD.Base.Vector(0, 0, 0))
            return

        # WedgeAngle > 0: build wedge shape via boolean cut
        # Extra height accounts for the thick-side extension caused by the tilt
        extra = R * abs(sin(radians(wa))) + 0.1  # small safety margin
        cyl = Part.makeCylinder(R, Thk + extra, FreeCAD.Base.Vector(0, 0, 0))

        # Large cutting box starting at z=Thk, extending upward
        big = 4 * (R + Thk + extra)
        cut_box = Part.makeBox(
            big, big, big,
            FreeCAD.Base.Vector(-big / 2, -big / 2, Thk)
        )

        # Rotate cutting box around Y-axis at (0, 0, Thk)
        # Right-hand rule: positive angle → +X side goes down → thinner at +X
        # This matches the pyoptools convention: S2 rotated around Y at (0,0,thickness)
        cut_box.rotate(
            FreeCAD.Base.Vector(0, 0, Thk),
            FreeCAD.Base.Vector(0, 1, 0),
            wa
        )

        obj.Shape = cyl.cut(cut_box)


def InsertRM(Ref=100, Th=10, D=50, ID="L", matcat="", matref="", WedgeAngle=0.0):
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    RoundMirrorPart(myObj, Ref, Th, D, matcat, matref, WedgeAngle)
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

def migrate_to_v2(obj):
    # Add the WedgeAngle property
    obj.ObjectVersion = 2

    _wrn("Migrating round mirror from v1 to v2\n")
    
    obj.addProperty(
        "App::PropertyAngle", "WedgeAngle", "Shape", "Wedge angle"
    )
    obj.WedgeAngle = 0.0
    