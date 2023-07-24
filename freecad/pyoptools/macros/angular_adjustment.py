import FreeCAD
import FreeCADGui
# from .wbcommand import *
from freecad.pyoptools.pyOpToolsWB.wbcommand import *
from freecad.pyoptools.pyOpToolsWB.qthelpers import outputDialog
from freecad.pyoptools.pyOpToolsWB.pyoptoolshelpers import getActiveSystem
from PySide import QtCore, QtGui
from scipy.optimize import minimize
from numpy import dot
from math import inf, degrees

def center_rot(drot, sen, el):
    """Auxiliary function to be used in an optimization algorithm

    Parameters
    ----------
    drot : tuple of floats
        Vector with the 3 euler angles used to reposition the element el.
    sen: str
        Label that identifies the sensor to be used to measure.
    el: str
        Label that identifies the element to be rotated.

    The element ``el`` is positioned using the angles specified by ``drot``,
    and then the system is propagated. The distance of the intersection point
    from the first ray in ``sen.hil_list`` to ``sen`` origin is returned.

    This function modifies the freecad-pyoptool objects before obtaining the
    pyoptools ``System`` and as far as some small tests were made, is too slow.
    It is better to use the center_rot_pot() for any optimization.
    """
    myObj = FreeCAD.ActiveDocument.getObjectsByLabel(el)[0]

    base = myObj.Placement.Base
    rot = myObj.Placement.Rotation
    Rz, Ry, Rx = rot.toEuler()

    drx, dry, drz = drot

    new_pos = FreeCAD.Placement(base, FreeCAD.Rotation(Rz+drz, Ry+dry, Rx+drx))

    myObj.Placement = new_pos

    S, R = getActiveSystem()
    S.ray_add(R)
    S.propagate()
    myObj.Placement = FreeCAD.Placement(base, rot)
    hit = S[sen][0].hit_list[0][0]
    print(hit, drot)
    return dot(hit, hit)**.5


def center_rot_pot(drot, S, R, sen, el):
    """Auxiliary function to be used in an optimization algorithm

    Parameters
    ----------

    drot : tuple of floats
        Vector with the 3 euler angles used to reposition the element el.
    S: pyoptools System
    sen: str
        Label that identifies the sensor to be used to measure.
    el: str
        Label that identifies the element to be rotated.

    The element ``el`` is positioned using the angles specified by ``drot``,
    and then the ``S`` system is propagated. The distance of the intersection
    point from the first ray in ``sen.hil_list`` to ``sen`` origin is returned.
    """

    S.reset()
    C, P, D = S.complist[el]

    S.complist[el] = C, P, drot
    S.ray_add(R)
    S.propagate()

    hl = S[sen][0].hit_list

    if hl:
        hit = hl[0][0]
    else:
        hit = inf
    print( dot(hit, hit)**.5,hit, drot)
    return dot(hit, hit)**.5

class RotationGUI(WBCommandGUI):
    def __init__(self):
        WBCommandGUI.__init__(self,'Rotation.ui')

        self.form.btnRay.clicked.connect(self.getRay)
        self.form.btnSensor.clicked.connect(self.getSensor)
        self.form.btnComponent.clicked.connect(self.getComponent)

        self.form.txtRaysource.editingFinished.connect(self.checkRay)
        self.form.txtSensor.editingFinished.connect(self.checkSensor)
        self.form.txtComponent.editingFinished.connect(self.checkComponent)


    def getRay(self, *args):
        obj = FreeCADGui.Selection.getSelection()[0]
        self.form.txtRaysource.setText(obj.Label)
        self.checkRay()

    def getSensor(self, *args):
        obj = FreeCADGui.Selection.getSelection()[0]
        self.form.txtSensor.setText(obj.Label)
        self.checkSensor()


    def getComponent(self, *args):
        obj = FreeCADGui.Selection.getSelection()[0]
        self.form.txtComponent.setText(obj.Label)
        self.checkComponent()

    def checkRay(self, *args):
        try:
            obj = FreeCAD.ActiveDocument.getObjectsByLabel(self.form.txtRaysource.text())[0]
        except IndexError:
            outputDialog("Object {} not found".format(self.form.txtRaysource.text()))
            self.form.txtRaysource.setText("")
            return False

        if not hasattr(obj, "cType"):
            outputDialog("Object {} not recognized by pyoptools, ignored.".format(obj.Label))
            self.form.txtRaysource.setText("")
            return False

        if obj.cType != "Ray":
            outputDialog("Please select a 'Ray' instance, not a '{}'".format(obj.cType))
            self.form.txtRaysource.setText("")
            return False
        return True

    def checkSensor(self, *args):
        try:
            obj = FreeCAD.ActiveDocument.getObjectsByLabel(self.form.txtSensor.text())[0]
        except IndexError:
            outputDialog("Object {} not found".format(self.form.txtSensor.text()))
            self.form.txtSensor.setText("")
            return False

        if not hasattr(obj, "cType"):
            outputDialog("Object {} not recognized by pyoptools, ignored.".format(obj.Label))
            self.form.txtSensor.setText("")
            return False

        if obj.cType != "Sensor":
            outputDialog("Please select a 'Sensor' instance, not a '{}'".format(obj.cType))
            self.form.txtSensor.setText("")
            return False
        return True

    def checkComponent(self, *args):
        try:
            obj = FreeCAD.ActiveDocument.getObjectsByLabel(self.form.txtComponent.text())[0]
        except IndexError:
            outputDialog("Object {} not found".format(self.form.txtComponent.text()))
            self.form.txtComponent.setText("")
            return False

        if not hasattr(obj, "cType"):
            outputDialog("Object {} not recognized by pyoptools, ignored.".format(obj.Label))
            self.form.txtSensor.setText("")
            return False

        return True

    def accept(self):

        if  not (self.checkComponent() and self.checkRay() and self.checkSensor()):
            return

        ray = self.form.txtRaysource.text()
        sensor = self.form.txtSensor.text()
        component = self.form.txtComponent.text()

        S, R = getActiveSystem()
        C, P, D = S[component]

        DR = minimize(center_rot_pot, D, (S, R, sensor, component), method="TNC")
        DR = DR.x

        myObj = FreeCAD.ActiveDocument.getObjectsByLabel(component)[0]

        base = myObj.Placement.Base
        rot = myObj.Placement.Rotation
        print("***", D)
        print("***", DR)
        print(degrees(DR[0]),degrees(DR[1]),degrees(DR[2]))
        newrot = FreeCAD.Rotation(degrees(DR[2]),degrees(DR[1]),degrees(DR[0]))

        print(rot.toEuler())
        print(newrot.toEuler())

        new_pos = FreeCAD.Placement(base, newrot)

        rv = outputDialog(\
            "Optimization Finished.\n"
            "Old rotation: {:8.2f}, {:8.2f}, {:8.2f}\n"
            "New rotation: {:8.2f}, {:8.2f}, {:8.2f}\n\n"
            "Do you want to update the design".format(
                degrees(D[0]), degrees(D[1]), degrees(D[2]),
                degrees(DR[0]), degrees(DR[1]), degrees(DR[2])),
            True)

        if rv:
            myObj.Placement = new_pos

        FreeCADGui.Control.closeDialog()

print("Warning, This tool does not use the selected ray source. Right now it uses all the active")
panel = RotationGUI()
FreeCADGui.Control.showDialog(panel)
