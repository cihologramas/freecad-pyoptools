import os
import FreeCADGui as Gui
import FreeCAD
from freecad.pyoptools import ICONPATH


class PyOpToolsWorkbench(Gui.Workbench):
    """
    class which gets initiated at startup of the gui
    """

    MenuText = "pyoptools workbench"
    ToolTip = "pyoptools worlbench"
    Icon = os.path.join(ICONPATH, "pyoptools.png")
    toolbox = []

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        This function is called at the first activation of the workbench.
        here is the place to import all the commands
        """
        from . import pyOpToolsWB

        self.appendToolbar("Propagation", ["btnPropagate", "btnWipe"])

        self.appendMenu(["Add Components"], "CatalogComponent")

        self.appendMenu(
            ["Add Components", "Lenses"],
            [
                "SphericalLens",
                "CylindricalLens",
                "DoubletLens",
                "ThickLens",
                "LensData",
                "PowellLens",
            ],
        )

        self.appendMenu(
            ["Add Components", "Mirrors"], ["RoundMirror", "RectangularMirror"]
        )

        self.appendMenu(
            ["Add Components", "Prisms"], ["PentaPrism", "DovePrism", "RightAnglePrism"]
        )

        self.appendMenu(["Add Components", "Beam Splitters"], ["BSCube"])

        self.appendMenu(
            ["Add Components", "Ray Sources"],
            ["RaysParallel", "RaysPoint", "RaysArray", "Ray"],
        )
        self.appendMenu(["Add Components"], "Aperture")
        self.appendMenu(["Add Components"], "DiffractionGratting")
        self.appendMenu(["Add Components"], "Sensor")

        self.appendMenu(["Simulate"], ["Propagate", "Reports", "Optimize"])

    def Activated(self):
        """
        code which should be computed when a user switch to this workbench
        """
        pass

    def Deactivated(self):
        """
        code which should be computed when this workbench is deactivated
        """
        pass


Gui.addWorkbench(PyOpToolsWorkbench())
