

import FreeCADGui
from sphericallens import SphericalLensMenu
from roundmirror import RoundMirrorMenu
from rayspoint import RaysPointMenu
from raysparallel import RaysParallelMenu
from propagate import PropagateMenu
from catalogcomponent import CatalogComponentMenu
from sensor import SensorMenu

FreeCADGui.addCommand('SphericalLens',SphericalLensMenu())
FreeCADGui.addCommand('RoundMirror',RoundMirrorMenu())
FreeCADGui.addCommand('RaysPoint',RaysPointMenu())
FreeCADGui.addCommand('RaysParallel',RaysParallelMenu())
FreeCADGui.addCommand('Propagate',PropagateMenu())
FreeCADGui.addCommand('CatalogComponent',CatalogComponentMenu())
FreeCADGui.addCommand('Sensor',SensorMenu())
