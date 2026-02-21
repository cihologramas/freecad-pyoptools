import FreeCADGui

from .sphericallens import SphericalLensMenu

FreeCADGui.addCommand("SphericalLens", SphericalLensMenu())

from .cylindricallens import CylindricalLensMenu

FreeCADGui.addCommand("CylindricalLens", CylindricalLensMenu())

from .roundmirror import RoundMirrorMenu

FreeCADGui.addCommand("RoundMirror", RoundMirrorMenu())

from .rectmirror import RectMirrorMenu

FreeCADGui.addCommand("RectangularMirror", RectMirrorMenu())

from .rayspoint import RaysPointMenu

FreeCADGui.addCommand("RaysPoint", RaysPointMenu())

from .raysparallel import RaysParallelMenu

FreeCADGui.addCommand("RaysParallel", RaysParallelMenu())

from .raysarray import RaysArrayMenu

FreeCADGui.addCommand("RaysArray", RaysArrayMenu())

from .ray import RayMenu

FreeCADGui.addCommand("Ray", RayMenu())

from .propagate import PropagateMenu

FreeCADGui.addCommand("Propagate", PropagateMenu())
FreeCADGui.addCommand("btnPropagate", PropagateMenu())

from .catalogcomponent import CatalogComponentMenu

FreeCADGui.addCommand("CatalogComponent", CatalogComponentMenu())

from .sensor import SensorMenu

FreeCADGui.addCommand("Sensor", SensorMenu())

from .spotdiagram import SpotDiagramMenu

FreeCADGui.addCommand("SpotDiagram", SpotDiagramMenu())
FreeCADGui.addCommand("btnSpotDiagram", SpotDiagramMenu())

from .doubletlens import DoubletLensMenu

FreeCADGui.addCommand("DoubletLens", DoubletLensMenu())

from .optimize import OptimizeMenu

FreeCADGui.addCommand("Optimize", OptimizeMenu())

from .thicklens import ThickLensMenu

FreeCADGui.addCommand("ThickLens", ThickLensMenu())

from .diffractiongratting import DiffractionGrattingMenu

FreeCADGui.addCommand("DiffractionGratting", DiffractionGrattingMenu())

from .aperture import ApertureMenu

FreeCADGui.addCommand("Aperture", ApertureMenu())

from .pentaprism import PentaPrismMenu

FreeCADGui.addCommand("PentaPrism", PentaPrismMenu())

from .doveprism import DovePrismMenu

FreeCADGui.addCommand("DovePrism", DovePrismMenu())

from .rightangleprism import RightAnglePrismMenu

FreeCADGui.addCommand("RightAnglePrism", RightAnglePrismMenu())


from .bscube import BSCubeMenu

FreeCADGui.addCommand("BSCube", BSCubeMenu())

from .powelllens import PowellLensMenu

FreeCADGui.addCommand("PowellLens", PowellLensMenu())

from .lensdata import LensDataMenu

FreeCADGui.addCommand("LensData", LensDataMenu())

from .simpledmd import SimpleDMDMenu

FreeCADGui.addCommand("SimpleDMD", SimpleDMDMenu())

from .positiononray import PositionOnRayMenu

FreeCADGui.addCommand("PositionOnRay", PositionOnRayMenu())

from .alignrotation import AlignRotationMenu

FreeCADGui.addCommand("AlignRotation", AlignRotationMenu())

from .positionmirroron2rays import PositionMirrorOn2RaysMenu

FreeCADGui.addCommand("PositionMirrorOn2Rays", PositionMirrorOn2RaysMenu())

from .about import AboutMenu

FreeCADGui.addCommand("AboutPyOpTools", AboutMenu())

from .utils import WipeMenu, EnableComponentsMenu, DisableComponentsMenu

FreeCADGui.addCommand("btnWipe", WipeMenu())
FreeCADGui.addCommand("EnableComponents", EnableComponentsMenu())
FreeCADGui.addCommand("DisableComponents", DisableComponentsMenu())
