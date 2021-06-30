# Macro to delete oll the propagations and rays, to clean the workspace
import FreeCAD
from pyOpToolsWB.qthelpers import outputDialog

yn = outputDialog("Are you sure?", True)
if yn:
    objs = FreeCAD.ActiveDocument.Objects
    todelete = []
    for obj in objs:
        if hasattr(obj, "cType"):
            if obj.cType == "Propagation":
                print("removing Propagation")
                todelete.append(obj.Label)
                continue
        if obj.isDerivedFrom("App::DocumentObjectGroup"):
            print("InGro")
            for iobj in obj.Group:
                if "Ray" in iobj.Label:  # Hay que hacer esto mejor
                    todelete.append(iobj.Label)
                    todelete.append(obj.Label)
                    break
    for obj in todelete:
        FreeCAD.ActiveDocument.removeObject(obj)
print(__name__)
