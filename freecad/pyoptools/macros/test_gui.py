
import FreeCADGui
from PySide import QtGui,QtCore
from pyOpToolsWB.qthelpers import outputDialog
from pivy import coin
from pivy import coin
import FreeCAD
import threading




class Gate:
    """
    Class that define which elements can be selected.
    Used with: FreeCADGui.Selection.addSelectionGate(Gate())
    https://forum.freecadweb.org/viewtopic.php?t=6229
    """
    def __init__(self):
        self.ok = False

    def allow(self,doc,obj,sub):
        #print(hasattr(obj,"cType"))
        #print(obj,type(obj))
        #print(sub,type(sub))
        return hasattr(obj,"cType")


# Mirar si con esto la seleccion se puede hacer mejor
class SelObserver:

    def __init__(self):
        view = FreeCADGui.ActiveDocument.ActiveView
        self.root = view.getSceneGraph()

    def addSelection(self,doc,obj,sub,pnt):
        Gui.Selection.clearSelection()
        print("addSelection")

    def removeSelection(self,doc,obj,sub):
        print ("removeSelection")
    def setSelection(self,doc):
        print ("setSelection")
    def clearSelection(self,doc):
        print("clearSelection")


# Mirar mejor https://wiki.freecadweb.org/index.php?title=Code_snippets#Function_resident_with_the_mouse_click_action
# https://github.com/yorikvanhavre/FreeCAD/blob/master/src/Mod/TemplatePyMod/TaskPanel.py

def isLine(edge):
    """Some ideas taken from a2plib.py from A2+ workbench"""
    if not hasattr(edge,"Curve"):
        return False
    if isinstance(edge.Curve, Part.Line):
        return True
    return False




def getFilePath(relativefilename, targetfile):
    return os.path.join(os.path.join(os.path.split(os.path.dirname(relativefilename))[0], "GUI"),targetfile)



class EventLogger(QtCore.QObject):
    def eventFilter(self, obj, event):
        print(event)
        return QtCore.QObject.eventFilter(self, obj, event)


class placementWidget(QtGui.QWidget):
    def __init__(self):
        super(placementWidget, self).__init__()
        self.initUI()
        self.so = None

    def initUI(self):
        fn1 = getFilePath(__file__, "positionWidget.ui")
        self.ui = FreeCADGui.PySideUic.loadUi(fn1, self)
        self.setLayout(self.ui.mainLayout)

        self.ui.orienCap.toggled.connect(self.getOrientation)
        self.ui.posCap.toggled.connect(self.getPosition)

        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.snap_point=None

        view = FreeCADGui.ActiveDocument.ActiveView
        self.root = view.getSceneGraph()
        #view.addEventCallbackPivy( coin.SoLocation2Event.getClassTypeId(), self.mouse_over_cb )


    def hideEvent(self, event):
        event.accept() # let the window close
        self.clearEvents()

    def registerEvents(self):
        if self.so is None:
            self.so = SelObserver()
            self.gate=Gate()
            FreeCADGui.Selection.addSelectionGate(self.gate)
            FreeCADGui.Selection.addObserver(self.so)
            self.mouse_over=self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.mouse_over_cb )
            self.mouse_click=self.view.addEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.mouse_click_cb )

    def clearEvents(self):
        if self.so is not None:
            FreeCADGui.Selection.removeObserver(self.so)
            Gui.Selection.removeSelectionGate()
            self.view.removeEventCallbackPivy( coin.SoLocation2Event.getClassTypeId(), self.mouse_over)
            self.view.removeEventCallbackPivy( coin.SoMouseButtonEvent.getClassTypeId(), self.mouse_click)
            self.so = None

        if self.snap_point is not None:
            self.root.removeChild(self.SnapNode)
            self.snap_point = None



    def getOrientation(self,checked):
        self.clearEvents()
        if checked:
            self.ui.posCap.setChecked(False)
            self.registerEvents()
        else:
            pass

    def getPosition(self,checked):
        self.clearEvents()
        if checked:
            print("add")
            self.ui.orienCap.setChecked(False)
            self.registerEvents()
        else:
            pass

    def draw_snap(self, sel, sensor):
        """Method that draw the current snap point"""

        if self.snap_point!=sel:
            if self.snap_point is not None:
                self.root.removeChild(self.SnapNode)
            self.snap_point=sel
            if sel is not None:
                col = coin.SoBaseColor()
                col.rgb = (0, 1, 0)
                trans = coin.SoTranslation()
                trans.translation.setValue(sel)
                snap = coin.SoMarkerSet()  # this is the marker symbol
                snap.markerIndex = FreeCADGui.getMarkerIndex("", 9)
                #cub = coin.SoSphere()
                self.SnapNode = coin.SoSeparator()
                self.SnapNode.addChild(col)
                self.SnapNode.addChild(trans)
                self.SnapNode.addChild(snap)
                self.root.addChild(self.SnapNode)


    def mouse_over_cb(self,event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition().getValue()
        listObjects = FreeCADGui.ActiveDocument.ActiveView.getObjectsInfo((int(pos[0]),int(pos[1])))
        if listObjects:
            # Take the closest object to the mouse
            obj = listObjects[0]
            fcobj = App.ActiveDocument.getObject(obj["Object"])
            fccmp = fcobj.Shape.getElement(obj["Component"])
            if self.gate.allow(None,fcobj,fccmp) and isLine(fccmp):
                x=obj["x"]
                y=obj["y"]
                z=obj["z"]

                pc=FreeCAD.Vector(x,y,z)
                p0=fccmp.Vertexes[0].Point
                p1=fccmp.Vertexes[1].Point
                print(fccmp)
                print(dir(fccmp))

                if ((pc-p0).Length) < ((pc-p1).Length):
                    # because of coin3d limitations, an scene can not be modified
                    # inside an event handler. So a Sensor must be used, to
                    # queue the  draw_snap method for later.
                    # The "self", can not be removed because the sensor is garbage
                    # collected as soon as mouse_over_cb is finished, and the
                    # method draw_snap is never called.

                    self.ts = coin.SoOneShotSensor(self.draw_snap,p0)
                    self.ts.schedule()
                else:
                    self.ts = coin.SoOneShotSensor(self.draw_snap,p1)
                    self.ts.schedule()
            else:
                self.ts = coin.SoOneShotSensor(self.draw_snap,None)
                self.ts.schedule()
    def mouse_click_cb(self, event_callback):
        if self.snap_point is not None:
            if self.ui.posCap.isChecked():
                self.ui.X.setValue(self.snap_point.x)
                self.ui.Y.setValue(self.snap_point.y)
                self.ui.Z.setValue(self.snap_point.z)


class WBCommandGUI:
    def __init__(self):
        fn = getFilePath(__file__, "TestGui.ui")
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

panel = WBCommandGUI()
FreeCADGui.Control.showDialog(panel)
