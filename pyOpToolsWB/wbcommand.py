import os
import FreeCAD,FreeCADGui

def getFilePath(relativefilename, targetfile):
    return os.path.join(os.path.join(os.path.split(os.path.dirname(relativefilename))[0], "GUI"),targetfile)

class WBCommandGUI:
    def __init__(self,gui):
        fn = getFilePath(__file__, gui)
        self.form = FreeCADGui.PySideUic.loadUi(fn)

class WBCommandMenu:
    def __init__(self,gui):
        self.gui=gui
    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
            return False
        else:
            return True

    def Activated(self):
        sl=self.gui()
        FreeCADGui.Control.showDialog(sl)

class WBPart:
    def __init__(self,obj,PartType):
        obj.Proxy = self
        obj.addProperty("App::PropertyString","cType").cType =PartType

    def onChanged(self, obj, prop):
        #Esto se necesita para cuando se carga de un archivo
        if prop =="cType":
            obj.setEditorMode("cType", 2)

    def pyoptools_repr(self, obj):
        print "pyOpTools representation of Object {} not implemented".format(obj.cType)
