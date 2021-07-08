# -*- coding: utf-8 -*-

"""Helper classes used in the workbench creation."""

import FreeCAD
import FreeCADGui
from freecad.pyoptools.pyOpToolsWB.qthelpers import getUIFilePath
from PySide import QtGui


class widgetMix(QtGui.QDialog):
    """Class to emulate a QDialog where multiple widgets behave as one.

    This class has an addWidget method, that allows to "merge" the widgets so
    they behave as if all the widget definitions belong to one single widget.
    If the widget is passed with a "name", the attributes of such widget will
    appear inside an attribute of the widgetMix. This allows to include in the
    same widget, several copies of one widget, and be able to access the
    attributes of such widgets independently.
    """

    def __init__(self, parent=None):
        super(widgetMix, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.widgets = []
        self.extra_attribs = {}

    def addWidget(self, w, name=None):
        """Add a widget to the widget mix.

        Parameters
        ----------

        w : QWidget
            Widget to add to the widgetMix
        name : str or None
            If not given (or none), the attributes of w will be accesible
            directly from the widgetMix. Care must be taken as if multiple
            widgets with the same attributes are added, only the attribute from
            the first widget added wil be accesible shadowing the others. This
            can be solved by giving the widget a "name", so it will be
            accesible as "widgetMix.name".

        TODO:
        -----
        No revision is made to avoid attributes shadowing. This must
        be fixed in the future.
        """

        self.layout.addWidget(w)
        if name is None:
            self.widgets.append(w)
        elif isinstance(name, str):
            self.extra_attribs[name] = w

    def __getattr__(self, name):
        """Get the attrubutes from the registered widgets."""
        # Check first in the widgets regostared with no name
        for w in self.widgets:
            try:
                return getattr(w, name)
            except AttributeError:
                pass
        try:
            return self.extra_attribs[name]
        except KeyError:
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
                elif isinstance(w, dict):
                    for name, nw in w.items():
                        self.form.addWidget(nw, name)
                else:
                    raise ValueError
        else:
            raise ValueError


class WBCommandMenu:
    def __init__(self, gui):
        self.gui = gui

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
            return False
        else:
            return True

    def Activated(self):
        sl = self.gui()
        FreeCADGui.Control.showDialog(sl)


class WBPart:
    def __init__(self, obj, PartType, enabled=True, reference="", notes=""):
        obj.Proxy = self
        obj.addProperty("App::PropertyString", "cType").cType = PartType
        obj.addProperty("App::PropertyBool", "enabled").enabled = enabled
        obj.addProperty(
            "App::PropertyString", "Reference"
        ).Reference = reference
        obj.addProperty("App::PropertyString", "Notes").Notes = notes

    def onChanged(self, obj, prop):
        # this method should not be overloaded. Overload propertyChanged instead

        # Esto se necesita para cuando se carga de un archivo
        if prop == "cType":
            obj.setEditorMode("cType", 2)

        if prop == "enabled":

            if obj.enabled:
                obj.ViewObject.Transparency = 30
            else:
                obj.ViewObject.Transparency = 90

        self.propertyChanged(obj, prop)

    def propertyChanged(self, obj, prop):
        # this method should be overloaded instead of onChanged
        pass

    def pyoptools_repr(self, obj):
        print(
            "pyOpTools representation of Object {} not implemented".format(
                obj.cType
            )
        )
