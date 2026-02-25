import os
import FreeCADGui as Gui
import FreeCAD
from freecad.pyoptools import ICONPATH
from PySide import QtCore


class PyOpToolsWorkbench(Gui.Workbench):
    """
    class which gets initiated at startup of the gui
    """

    MenuText = "pyoptools workbench"
    ToolTip = "pyoptools workbench"
    Icon = os.path.join(ICONPATH, "pyoptools.png")
    toolbox = []
    light_sources_panel = None
    sensors_panel = None

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        This function is called at the first activation of the workbench.
        here is the place to import all the commands
        """
        from . import pyOpToolsWB

        # Propagation toolbar - includes optimization button (Story 1.2)
        self.appendToolbar("Propagation", ["btnPropagate", "btnWipe", "Optimize"])

        # Components toolbar - catalog browser with integrated search (Epic 2)
        self.appendToolbar("Components", ["CatalogComponent"])

        # Tools toolbar - ray-based positioning commands, component enable/disable, and spot diagram
        self.appendToolbar(
            "Tools",
            ["EnableComponents", "DisableComponents", "btnSpotDiagram", "PositionOnRay", "AlignRotation", "PositionMirrorOn2Rays"],
        )

        # Add Components menu - reorganized per Story 1.1
        # Lenses submenu (6 components)
        self.appendMenu(
            ["Add Components", "Lenses"],
            [
                "SphericalLens",
                "CylindricalLens",
                "DoubletLens",
                "ThickLens",
                "PowellLens",
                "LensData",
            ],
        )

        # Mirrors submenu (2 components)
        self.appendMenu(
            ["Add Components", "Mirrors"], ["RoundMirror", "RectangularMirror"]
        )

        # Prisms submenu (4 components)
        self.appendMenu(
            ["Add Components", "Prisms"],
            ["PentaPrism", "DovePrism", "RightAnglePrism", "BSCube"],
        )

        # Optical Elements submenu (2 components)
        self.appendMenu(
            ["Add Components", "Optical Elements"],
            ["DiffractionGratting", "Aperture", "SimpleDMD"],
        )

        # Sensors submenu (1 component)
        self.appendMenu(["Add Components", "Sensors"], ["Sensor"])

        # Ray Sources submenu (4 components)
        self.appendMenu(
            ["Add Components", "Ray Sources"],
            ["Ray", "RaysPoint", "RaysParallel", "RaysArray"],
        )

        # From Catalog menu item (includes integrated search - Epic 2)
        self.appendMenu(["Add Components"], "CatalogComponent")

        # Simulate menu - reorganized per Story 1.1
        self.appendMenu(["Simulate"], ["Propagate", "btnWipe", "Optimize"])

        # Tools menu - spot diagram, component enable/disable, and ray-based positioning commands
        self.appendMenu(
            ["Tools"],
            ["SpotDiagram", "EnableComponents", "DisableComponents", "PositionOnRay", "AlignRotation", "PositionMirrorOn2Rays"],
        )

        # Help menu - append to FreeCAD's existing Help menu
        self.appendMenu(["&Help"], ["AboutPyOpTools"])

    def Activated(self):
        """
        code which should be computed when a user switch to this workbench
        """
                
        # Create and show Light Sources panel (docked on right side)
        if self.light_sources_panel is None:
            from .pyOpToolsWB.lightsourcespanel import LightSourcesPanel
            
            mw = Gui.getMainWindow()
            self.light_sources_panel = LightSourcesPanel()
            mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.light_sources_panel)
        
        # Create and show Sensors panel (docked on right side, tabbed with Light Sources)
        if self.sensors_panel is None:
            from .pyOpToolsWB.sensorspanel import SensorsPanel
            
            mw = Gui.getMainWindow()
            self.sensors_panel = SensorsPanel()
            mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.sensors_panel)
            # Tab it with the light sources panel
            mw.tabifyDockWidget(self.light_sources_panel, self.sensors_panel)

    def Deactivated(self):
        """
        code which should be computed when this workbench is deactivated
        """
        # Hide the Light Sources panel when switching workbenches
        if self.light_sources_panel is not None:
            self.light_sources_panel.hide()
        
        # Hide the Sensors panel when switching workbenches
        if self.sensors_panel is not None:
            self.sensors_panel.hide()


Gui.addWorkbench(PyOpToolsWorkbench())
