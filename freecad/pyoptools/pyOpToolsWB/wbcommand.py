# -*- coding: utf-8 -*-
import FreeCAD
import FreeCADGui
from pyOpToolsWB.qthelpers import getUIFilePath
from PySide import QtGui


class widgetMix(QtGui.QDialog):
    def __init__(self, parent=None):
        super(widgetMix, self).__init__(parent)
        #self.setWindowTitle("My Form")
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.widgets = []

    def addWidget(self, w):
        self.layout.addWidget(w)
        self.widgets.append(w)

    def __getattr__(self, name):
        for w in self.widgets:
            try:
                return getattr(w, name)
            except AttributeError:
                pass
        raise AttributeError


class WBCommandGUI:
    def __init__(self, gui):

        if isinstance(gui, str):
            fn = getUIFilePath(gui)
            self.form = FreeCADGui.PySideUic.loadUi(fn)
        elif isinstance(gui, list):
            self.form = widgetMix()
            for w in gui:
                if isinstance(w, str):
                    fn = getUIFilePath(w)
                    nw = FreeCADGui.PySideUic.loadUi(fn)
                    self.form.addWidget(nw)
                elif isinstance(w, QtGui.QWidget):
                    self.form.addWidget(w)
                else:
                    raise ValueError
        else:
            raise ValueError

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
        print("pyOpTools representation of Object {} not implemented".format(obj.cType))
