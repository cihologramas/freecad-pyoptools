import FreeCADGui

from sphericallens import SphericalLensMenu
FreeCADGui.addCommand('SphericalLens',SphericalLensMenu())

from roundmirror import RoundMirrorMenu
FreeCADGui.addCommand('RoundMirror',RoundMirrorMenu())

from rayspoint import RaysPointMenu
FreeCADGui.addCommand('RaysPoint',RaysPointMenu())

from raysparallel import RaysParallelMenu
FreeCADGui.addCommand('RaysParallel',RaysParallelMenu())

from propagate import PropagateMenu
FreeCADGui.addCommand('Propagate',PropagateMenu())

from catalogcomponent import CatalogComponentMenu
FreeCADGui.addCommand('CatalogComponent',CatalogComponentMenu())

from sensor import SensorMenu
FreeCADGui.addCommand('Sensor',SensorMenu())

from reports import ReportsMenu
FreeCADGui.addCommand('Reports',ReportsMenu())

from doubletlens import DoubletLensMenu
FreeCADGui.addCommand('DoubletLens',DoubletLensMenu())