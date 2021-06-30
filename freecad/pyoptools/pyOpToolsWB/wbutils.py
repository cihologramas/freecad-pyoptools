# File that contains some utilities that simplify the design of systems


import FreeCAD
from pyOpToolsWB.qthelpers import outputDialog

class WipeMenu:
    """
    Command to wipe (erase propagations and rays) from the system
    """
    def GetResources(self):
        return {"MenuText": "Wipe",
                "ToolTip": "Delete propagations and rays",
                "Pixmap": ""}

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
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
