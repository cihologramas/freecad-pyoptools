# -*- coding: utf-8 -*-
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
    def __init__(self,obj,PartType,enabled = True, reference ="",notes =""):
        obj.Proxy = self
        obj.addProperty("App::PropertyString","cType").cType = PartType
        obj.addProperty("App::PropertyBool","enabled").enabled = enabled
        obj.addProperty("App::PropertyString","Reference").Reference = reference
        obj.addProperty("App::PropertyString","Notes").Notes = notes
    def onChanged(self, obj, prop):
        #this method should not be overloaded. Overload propertyChanged instead

        #Esto se necesita para cuando se carga de un archivo
        if prop =="cType":
            obj.setEditorMode("cType", 2)

        if prop =="enabled":

            if obj.enabled:
                obj.ViewObject.Transparency = 30
            else:
                obj.ViewObject.Transparency = 90

        self.propertyChanged(obj,prop)

    def propertyChanged(self,obj,prop):
        # this method should be overloaded instead of onChanged
        pass


    def pyoptools_repr(self, obj):
        print "pyOpTools representation of Object {} not implemented".format(obj.cType)
