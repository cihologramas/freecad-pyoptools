# Macro to delete all the propagations and rays, to clean the workspace
import FreeCAD, FreeCADGui
from pyOpToolsWB.qthelpers import outputDialog
from math import radians


def isLine(edge):
    """Some ideas taken from a2plib.py from A2+ workbench"""
    if not hasattr(edge,"Curve"):
        return False
    if isinstance(edge.Curve, Part.Line):
        return True
    return False


selections = FreeCADGui.Selection.getSelectionEx()[0] #Hay que verificar que solo haya un objeto seleccionado

selection = selections.SubObjects[0] # Hay que verificar que solo exista un objeto seleccionado

if isLine(selection):
    obj = FreeCAD.ActiveDocument.getObjectsByLabel("Mitutoyo")[0]

    m = obj.Placement
    print(selection.Vertexes[0])

    print(m)

    m.move(selection.Vertexes[0].Point-m.Base)

    print(m)

# m=FreeCAD.Matrix()
# m.rotateX(radians(0))
# m.rotateY(radians(0))
# m.rotateZ(radians(0))
# m.move((ray.Vertexes[0].X,ray.Vertexes[0].Y, ray.Vertexes[0].Z))
#

#
# FreeCAD.ActiveDocument.recompute()
