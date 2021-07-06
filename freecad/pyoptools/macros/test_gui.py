
import FreeCADGui
from PySide import QtGui,QtCore
from pyOpToolsWB.qthelpers import getUIFilePath
from pyOpToolsWB.widgets.placementWidget import placementWidget
from pyOpToolsWB.wbcommand import WBCommandGUI as WBC
from pivy import coin
import FreeCAD
import threading


class WBCommandGUI:
    def __init__(self):
        fn = getUIFilePath("TestGui.ui")
        print(fn)
        self.form = FreeCADGui.PySideUic.loadUi(fn)
        inst = placementWidget()
        #elogger=EventLogger(self.form.verticalLayout)
        #inst.installEventFilter(elogger)
        self.form.verticalLayout.addWidget(inst)

        #self.s =SelObserver()
        #FreeCADGui.Selection.addObserver(self.s)                       # install the function mode resident
        #FreeCADGui.Selection.removeObserver(s)
        #FreeCADGui.Selection.addSelectionGate("SELECT Part::Feature SUBELEMENT Edge")
        ####FreeCADGui.Selection.addSelectionGate(Gate())

        #self.view = FreeCADGui.ActiveDocument.ActiveView


        # to remove Callback :
        #view.removeEventCallbackPivy( coin.SoLocation2Event.getClassTypeId(), mouse_over)
    #https://forum.freecadweb.org/viewtopic.php?t=19072



    #view = FreeCADGui.ActiveDocument.ActiveView


    def accept(self):
        print("accept")
        print(self.form.verticalLayout.itemAt(0).widget().ui.X.value())
        #FreeCADGui.Selection.removeObserver(self.s)
        ###Gui.Selection.removeSelectionGate()
        FreeCADGui.Control.closeDialog()
        #self.view.removeEventCallbackPivy( coin.SoLocation2Event.getClassTypeId(), self.mouse_over)

    def reject(self):
        print("cancel")
        #FreeCADGui.Selection.removeObserver(self.s)
        #self.view.removeEventCallbackPivy( coin.SoLocation2Event.getClassTypeId(), self.mouse_over)
        ##Gui.Selection.removeSelectionGate()
        return True
class ApertureGUI(WBC):
    def __init__(self):
        inst = placementWidget()
        WBC.__init__(self,[inst, 'Aperture.ui'])

    def accept(self):
        print(self.form.Xpos.value())

panel = ApertureGUI()

FreeCADGui.Control.showDialog(panel)
