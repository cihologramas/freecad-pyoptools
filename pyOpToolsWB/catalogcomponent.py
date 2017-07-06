from PySide import QtGui
from wbcommand import *
from pyoptools.raytrace.library import library
from pyoptools.raytrace.mat_lib.material import find_material
from sphericallens import InsertSL
from math import radians

class CatalogComponentGUI(WBCommandGUI):
    def __init__(self):
        WBCommandGUI.__init__(self,'CatalogComponent.ui')

        for lib in dir(library):
            c=getattr(library,lib)
            if isinstance(c,library.Library):
                self.form.Catalog.addItem(lib,sorted(c.parts()))

        self.catalogChange(0)
        self.referenceChange(0)

        self.form.Catalog.currentIndexChanged.connect(self.catalogChange)
        self.form.Reference.currentIndexChanged.connect(self.referenceChange)


    def catalogChange(self,*args):

        while self.form.Reference.count():
            self.form.Reference.removeItem(0)

        for reference in self.form.Catalog.itemData(args[0]):
            red = QtGui.QPixmap(16, 16)
            red.fill(QtGui.QColor("red"))
            green = QtGui.QPixmap(16, 16)
            green.fill(QtGui.QColor("green"))

            if self.is_available(self.form.Catalog.currentText(),reference):
                color = green
            else:
                color = red

            self.form.Reference.addItem(color,reference)
            #item.setStyleSheet("color: green")

    def is_available(self,catalog,reference):
        #catalog = self.form.Catalog.currentText()
        #reference = self.form.Reference.currentText()
        lib=getattr(library,catalog)
        ok=True
        comp_type = lib.parser.get(reference,"type")
        if comp_type == "SphericalLens":
            comp_mat = lib.parser.get(reference,"material")
            matlibs=find_material(comp_mat)
            if len(matlibs)==0:
                ok=False

        else:
            ok=False
        return ok

    def referenceChange(self,*args):
        catalog = self.form.Catalog.currentText()
        lib=getattr(library,catalog)
        reference = self.form.Reference.currentText()
        options = lib.parser.options(reference)
        self.form.Info.clear()
        for option in options:
            self.form.Info.insertPlainText("{} = {}\n".format(option, lib.parser.get(reference,option)))

        ok=self.is_available(catalog, reference)
        if ok:
            self.form.Status.setText("Component Available")
            self.form.Status.setStyleSheet("color: green")
        else:
            self.form.Status.setText("Component not Available")
            self.form.Status.setStyleSheet("color: red")


    def accept(self):
        catalog = self.form.Catalog.currentText()
        reference = self.form.Reference.currentText()

        if self.is_available(catalog,reference):

            lib=getattr(library,catalog)
            comptype = lib.parser.get(reference,"type")
            X=self.form.Xpos.value()
            Y=self.form.Ypos.value()
            Z=self.form.Zpos.value()
            Xrot=self.form.Xrot.value()
            Yrot=self.form.Yrot.value()
            Zrot=self.form.Zrot.value()
            if comptype == "SphericalLens":
                mat = lib.parser.get(reference,"material")
                th = lib.parser.getfloat(reference,"thickness")
                diam = 2.* lib.parser.getfloat(reference,"radius")
                c1 =  lib.parser.getfloat(reference,"curvature_s1")
                c2 =  lib.parser.getfloat(reference,"curvature_s2")

                matcat = find_material(mat)[0]
                obj = InsertSL(c1,c2,th,diam,"L",matcat,mat)

                m=FreeCAD.Matrix()
                m.rotateX(radians(Xrot))
                m.rotateY(radians(Yrot))
                m.rotateZ(radians(Zrot))
                m.move((X,Y,Z))
                p1 = FreeCAD.Placement(m)
                obj.Placement = p1


            FreeCADGui.Control.closeDialog()

class CatalogComponentMenu:
    def GetResources(self):
        return {"MenuText": "Catalog Component",
                #"Accel": "Ctrl+M",
                "ToolTip": "Catalog Component",
                "Pixmap": ""}

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
            return False
        else:
            return True

    def Activated(self):
        sl=CatalogComponentGUI()
        FreeCADGui.Control.showDialog(sl)
