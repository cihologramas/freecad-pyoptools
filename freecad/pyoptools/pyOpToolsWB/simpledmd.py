# -*- coding: utf-8 -*-
"""Classes used to define a SimpleDMD (Digital Micromirror Device)."""

import FreeCAD
import FreeCADGui
import Part
import os

from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from .feedback import FeedbackHelper
from freecad.pyoptools import ICONPATH

import pyoptools.raytrace.comp_lib as comp_lib
from math import radians

_wrn = FreeCAD.Console.PrintWarning


class SimpleDMDGUI(WBCommandGUI):
    """GUI dialog for SimpleDMD component creation."""

    def __init__(self):
        pw = placementWidget()
        # Note: No materialWidget - SimpleDMD is 100% reflective
        WBCommandGUI.__init__(self, [pw, "SimpleDMD.ui"])

    @FeedbackHelper.with_error_handling("SimpleDMD")
    def accept(self):
        """Handle dialog acceptance - create SimpleDMD object."""
        # Extract geometry parameters
        width = self.form.Width.value()
        height = self.form.Height.value()
        thickness = self.form.Thickness.value()

        # Extract angle parameters (degrees from UI)
        tilt_angle = self.form.TiltAngle.value()
        on_dir = self.form.OnDirectionAngle.value()
        off_dir = self.form.OffDirectionAngle.value()
        state = self.form.State.currentText()  # "flat", "on", or "off"

        # Extract placement parameters
        X = self.form.Xpos.value()
        Y = self.form.Ypos.value()
        Z = self.form.Zpos.value()
        Xrot = self.form.Xrot.value()
        Yrot = self.form.Yrot.value()
        Zrot = self.form.Zrot.value()

        # Create SimpleDMD object (angles stored in degrees)
        obj = InsertSimpleDMD(
            width, height, thickness, tilt_angle, on_dir, off_dir, state, ID="DMD"
        )

        # Apply placement transformation
        m = FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X, Y, Z))
        obj.Placement = FreeCAD.Placement(m)

        # Decorator automatically handles:
        # - FreeCAD.ActiveDocument.recompute()
        # - FreeCADGui.updateGui()
        # - FreeCADGui.Control.closeDialog()


class SimpleDMDMenu(WBCommandMenu):
    """Menu command for SimpleDMD component."""

    def __init__(self):
        WBCommandMenu.__init__(self, SimpleDMDGUI)

    def GetResources(self):
        return {
            "MenuText": "SimpleDMD",
            "ToolTip": "Add SimpleDMD (Digital Micromirror Device)",
            "Pixmap": "",  # No icon (blank)
        }

    # Activated() inherited from WBCommandMenu


class SimpleDMDPart(WBPart):
    """FreeCAD Part representing SimpleDMD optical component.

    SimpleDMD (Digital Micromirror Device) is a programmable reflective surface
    with micro-mirrors that tilt to ON or OFF positions for spatial light modulation.

    This component wraps pyoptools SimpleDMDDevice, which provides a complete
    6-surface parallelepiped with active DMD on front face and optical stops
    on the other 5 faces.

    Properties
    ----------
    Width : PropertyLength
        DMD device width in X dimension (default 10.368mm - DLP4710 active area)
    Height : PropertyLength
        DMD device height in Y dimension (default 5.832mm - DLP4710 active area)
    Thickness : PropertyLength
        DMD device thickness in Z dimension (default 1.0mm - visual solid only)
    TiltAngle : float
        Tilt angle in degrees (angle between normal and Z-axis when tilted, default 17°)
    OnDirectionAngle : float
        Direction angle in degrees for ON state (CCW from +X, default 270°)
        NOTE: These angles appear inverted vs TI datasheet (our ON = TI OFF, our OFF = TI ON)
        This needs verification - behavior kept consistent with sample measurements
    OffDirectionAngle : float
        Direction angle in degrees for OFF state (CCW from +X, default 180°)
        NOTE: These angles appear inverted vs TI datasheet (our ON = TI OFF, our OFF = TI ON)
        This needs verification - behavior kept consistent with sample measurements
    State : Enumeration
        Current DMD state: "flat", "on", or "off"

    Notes
    -----
    - Angles stored in degrees for user convenience, converted to radians
      when creating pyoptools representation
    - Reflectivity is always 1.0 (100% reflective mirror) - not exposed as
      a user parameter since DMD mirrors are designed for perfect reflection
    - Origin is at center of front (active DMD) face at Z=0, with box
      extending in positive Z direction (from Z=0 to Z=+Thickness)
    - Centered in X and Y for intuitive rotation behavior
    - **IMPORTANT**: Direction angles appear inverted compared to TI datasheet
      (our ON direction = TI OFF direction, our OFF direction = TI ON direction).
      Current values (ON=270°, OFF=180°) are set to match observed sample behavior.
      This discrepancy needs verification and may require correction.
    """

    def __init__(
        self,
        obj,
        width=10.368,
        height=5.832,
        thickness=1.0,
        tilt_angle=17.0,
        on_direction_angle=270.0,
        off_direction_angle=180.0,
        state="off",
    ):
        WBPart.__init__(self, obj, "SimpleDMD")

        # Geometry properties
        obj.addProperty(
            "App::PropertyLength", "Width", "Shape", "DMD device width (X dimension)"
        )
        obj.addProperty(
            "App::PropertyLength", "Height", "Shape", "DMD device height (Y dimension)"
        )
        obj.addProperty(
            "App::PropertyLength",
            "Thickness",
            "Shape",
            "DMD device thickness (Z dimension)",
        )

        # Mirror angle properties (stored in degrees for user convenience)
        obj.addProperty(
            "App::PropertyFloat",
            "TiltAngle",
            "Mirror",
            "Tilt angle in degrees (0=flat, no tilt)",
        )
        obj.addProperty(
            "App::PropertyFloat",
            "OnDirectionAngle",
            "Mirror",
            "ON state direction angle in degrees (CCW from +X)",
        )
        obj.addProperty(
            "App::PropertyFloat",
            "OffDirectionAngle",
            "Mirror",
            "OFF state direction angle in degrees (CCW from +X)",
        )
        obj.addProperty(
            "App::PropertyEnumeration",
            "State",
            "Mirror",
            "DMD state: flat (neutral), on (tilted to ON), off (tilted to OFF)",
        )

        # Initialize property values
        obj.Width = width
        obj.Height = height
        obj.Thickness = thickness
        obj.TiltAngle = tilt_angle
        obj.OnDirectionAngle = on_direction_angle
        obj.OffDirectionAngle = off_direction_angle

        # Set enumeration options BEFORE setting value
        obj.State = ["flat", "on", "off"]
        obj.State = state

        # Visual properties (silver/gray mirror surface)
        obj.ViewObject.Transparency = 0
        obj.ViewObject.ShapeColor = (0.8, 0.8, 0.8, 0.0)

        # Version for migration support
        obj.ObjectVersion = 1

    def execute(self, obj):
        """Generate 3D geometry representing DMD device.

        Creates a rectangular box with front face at Z=0 (active DMD surface),
        extending in positive Z direction. Centered in X and Y.
        Adds "DMD" text on front surface for orientation reference.
        """
        # Create box with DMD dimensions
        # Origin at center of front face: centered in X,Y with front face at Z=0
        box = Part.makeBox(
            obj.Width.Value,
            obj.Height.Value,
            obj.Thickness.Value,
            FreeCAD.Vector(
                -obj.Width.Value / 2.0,
                -obj.Height.Value / 2.0,
                0,
            ),
        )

        # Add "DMD" text on front surface for orientation
        # Text orientation: D's line=left, M's peaks=up, D's curve=right
        try:
            font_path = os.path.join(ICONPATH, "LiberationMono-Bold.ttf")

            # Text size: 40% of smaller dimension for good visibility
            text_size = min(obj.Width.Value, obj.Height.Value) * 0.4

            # Create text wires directly (no document object created)
            wire_lists = Part.makeWireString("DMD", font_path, text_size, 0)

            # Build a compound of all wires for bounding box calculation
            all_wires = [w for char_wires in wire_lists for w in char_wires]
            wire_compound = Part.makeCompound(all_wires)

            # Mirror around YZ plane (flip X) so text is readable from Z-
            mirror_matrix = FreeCAD.Matrix()
            mirror_matrix.A11 = -1
            mirrored = wire_compound.transformGeometry(mirror_matrix)

            # Center on front face (Z=0)
            bb = mirrored.BoundBox
            mirrored.translate(
                FreeCAD.Vector(
                    -(bb.XMin + bb.XMax) / 2.0,
                    -(bb.YMin + bb.YMax) / 2.0,
                    0,
                )
            )

            # Extrude each wire into a solid
            text_solids = []
            for wire in mirrored.Wires:
                try:
                    face = Part.Face(wire)
                    text_solids.append(face.extrude(FreeCAD.Vector(0, 0, 0.01)))
                except Exception:
                    pass

            # Fuse text with box
            if text_solids:
                obj.Shape = box.cut(Part.makeCompound(text_solids))
            else:
                obj.Shape = box

        except Exception as e:
            _wrn(f"Could not create DMD text label: {e}\n")
            obj.Shape = box

    def pyoptools_repr(self, obj):
        """Convert to pyoptools SimpleDMDDevice representation.

        Converts angle properties from degrees (user-friendly) to radians
        (required by pyoptools API).

        Returns
        -------
        comp_lib.SimpleDMDDevice
            pyoptools SimpleDMDDevice component ready for ray tracing
        """
        # Convert angles from degrees to radians
        tilt_rad = radians(obj.TiltAngle)
        on_dir_rad = radians(obj.OnDirectionAngle)
        off_dir_rad = radians(obj.OffDirectionAngle)

        return comp_lib.SimpleDMDDevice(
            tilt_angle=tilt_rad,
            on_direction_angle=on_dir_rad,
            off_direction_angle=off_dir_rad,
            state=obj.State,
            width=obj.Width.Value,
            height=obj.Height.Value,
            thickness=obj.Thickness.Value,
        )

    def onDocumentRestored(self, obj):
        """Handle document restoration (version migration support).

        Called when loading saved documents. Future versions can add
        migration logic here.
        """
        # Call base class migration if needed
        WBPart.onDocumentRestored(self, obj)

        # No migration needed for ObjectVersion=1 (initial version)


def InsertSimpleDMD(
    width,
    height,
    thickness,
    tilt_angle,
    on_direction_angle,
    off_direction_angle,
    state,
    ID="DMD",
):
    """Create and insert SimpleDMD component into active document.

    Parameters
    ----------
    width : float
        DMD device width in mm
    height : float
        DMD device height in mm
    thickness : float
        DMD device thickness in mm
    tilt_angle : float
        Tilt angle in degrees
    on_direction_angle : float
        ON state direction in degrees (CCW from +X)
    off_direction_angle : float
        OFF state direction in degrees (CCW from +X)
    state : str
        Initial state: "flat", "on", or "off"
    ID : str, optional
        Object name/label (default "DMD")

    Returns
    -------
    FreeCAD.DocumentObject
        Created SimpleDMD object (ready for placement assignment)
    """
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", ID)
    SimpleDMDPart(
        myObj,
        width,
        height,
        thickness,
        tilt_angle,
        on_direction_angle,
        off_direction_angle,
        state,
    )
    myObj.ViewObject.Proxy = 0  # Standard for FeaturePython objects
    FreeCAD.ActiveDocument.recompute()
    return myObj
