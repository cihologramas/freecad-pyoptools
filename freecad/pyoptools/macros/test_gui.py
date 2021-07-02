
import FreeCADGui
from PySide import QtGui
from pyOpToolsWB.qthelpers import outputDialog


# Mirar si con esto la seleccion se puede hacer mejor
# class SelObserver:
#    def addSelection(self,doc,obj,sub,pnt):
#        print "addSelection"
#    def removeSelection(self,doc,obj,sub):
#        print "removeSelection"
#    def setSelection(self,doc):
#        print "setSelection"
#    def clearSelection(self,doc):
#        print "clearSelection"

#s=SelObserver()
#FreeCADGui.Selection.addObserver(s)
#FreeCADGui.Selection.removeObserver(s)

# Mirar mejor https://wiki.freecadweb.org/index.php?title=Code_snippets#Function_resident_with_the_mouse_click_action


def isLine(edge):
    """Some ideas taken from a2plib.py from A2+ workbench"""
    if not hasattr(edge,"Curve"):
        return False
    if isinstance(edge.Curve, Part.Line):
        return True
    return False




def getFilePath(relativefilename, targetfile):
    return os.path.join(os.path.join(os.path.split(os.path.dirname(relativefilename))[0], "GUI"),targetfile)

class placementWidget(QtGui.QWidget):
    def __init__(self):
        super(placementWidget, self).__init__()
        self.initUI()

    def initUI(self):
        fn1 = getFilePath(__file__, "positionWidget.ui")
        self.ui = FreeCADGui.PySideUic.loadUi(fn1, self)
        self.setLayout(self.ui.mainLayout)

        self.ui.orienCap.clicked.connect(self.getOrientation)
        self.ui.posCap.clicked.connect(self.getPosition)

    def getOrientation(self):
        print("geto")

    def getPosition(self):
        selections = FreeCADGui.Selection.getSelectionEx()
        if len(selections)==0:
            outputDialog("Select an object to capture its position")
            return
        if len(selections)>1:
            outputDialog("Select only one object")
            return

        selection = selections[0].SubObjects
        if len(selection)==0:
            outputDialog("Select an object to capture its position")
            return
        if len(selection)>1:
            outputDialog("Select only one object.")
            return

        selection = selection[0]
        print (dir(selection))
        if isLine(selection):
            print(selection.Vertexes[0].Point)
            print(selection.Vertexes[1].Point)


class WBCommandGUI:
    def __init__(self):
        fn = getFilePath(__file__, "TestGui.ui")

        self.form = FreeCADGui.PySideUic.loadUi(fn)
        inst = placementWidget()
        #i1=FreeCADGui.PySideUic.loadUi(fn1,self.form )
        #i1.show()
        self.form.verticalLayout.addWidget(inst)
        #print(dir(inst))
        #print(i1.doubleSpinBox.value())

panel = WBCommandGUI()
FreeCADGui.Control.showDialog(panel)
