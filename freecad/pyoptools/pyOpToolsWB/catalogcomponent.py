# -*- coding: utf-8 -*-
"""Classes used to define a component from different catalogs."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from PySide import QtGui
from pyoptools.raytrace.library import library
from pyoptools.raytrace.mat_lib import material
from .sphericallens import InsertSL
from .doubletlens import InsertDL
from .cylindricallens import InsertCL
from math import radians
from ast import literal_eval


class CatalogComponentGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "CatalogComponent.ui"])

        for catalog in library.catalogs():
            c = getattr(library, catalog)
            self.form.Catalog.addItem(catalog, sorted(c.parts()))

        # Dictionary to cache the material availability
        self.__material_available_cache__={}

        self.catalogChange(0)
        self.referenceChange(0)

        self.form.Catalog.currentIndexChanged.connect(self.catalogChange)
        self.form.Reference.currentIndexChanged.connect(self.referenceChange)

       

    def catalogChange(self, *args):

        self.form.Reference.clear()
        self.form.Reference.addItems(self.form.Catalog.itemData(args[0]))

        # Colocar los cuadros verdes y rojos para marcar si una componente está
        # disponible, se demora demasiado. Se comenta para no perder la idea
        # pero hay que hacerla diferente
        
        #red = QtGui.QPixmap(16, 16)
        #red.fill(QtGui.QColor("red"))
        #green = QtGui.QPixmap(16, 16)
        #green.fill(QtGui.QColor("green"))

        #for reference in self.form.Catalog.itemData(args[0]):    
        #    if self.is_available(self.form.Catalog.currentText(), reference):
        #        color = green
        #    else:
        #        color = red
        #    self.form.Reference.addItem(color, reference)
            # item.setStyleSheet("color: green")

    def is_material_available(self,reference):
        if reference in self.__material_available_cache__:
            rv =  self.__material_available_cache__[reference]
        else:
            try:
                mat = material[reference]
                self.__material_available_cache__[reference] = True;
                rv=True
            except KeyError:
                self.__material_available_cache__[reference] = False;
                rv=False

        return rv
        
    def is_available(self, catalog, reference):
        # catalog = self.form.Catalog.currentText()
        # reference = self.form.Reference.currentText()
        part_descriptor = getattr(library, catalog).descriptor(reference)
        ok = True
        comp_type = part_descriptor["type"]
        if comp_type == "SphericalLens":
            comp_mat = part_descriptor["material"]
            if not self.is_material_available(comp_mat):
                print("material {} not found".format(comp_mat))
                ok = False

        elif comp_type == "CylindricalLens":
            comp_mat = part_descriptor["material"]
            if not self.is_material_available(comp_mat):
                print("material {} not found".format(comp_mat))
                ok = False

        elif comp_type in ["Doublet", "AirSpacedDoublet"]:
            comp_mat1 = part_descriptor["material_l1"]
            comp_mat2 = part_descriptor["material_l2"]

            if not self.is_material_available(comp_mat1):
                print("material {} not found".format(comp_mat1))
                ok = False

            if not self.is_material_available(comp_mat2):
                print("material {} not found".format(comp_mat2))
                ok = False
        else:
            print("Component Type {} not found".format(comp_type))
            ok = False

        return ok

    def referenceChange(self, *args):
        catalog = self.form.Catalog.currentText()
        lib = getattr(library, catalog)
        reference = self.form.Reference.currentText()
        ## To avoid some errors raised when there is a catalog change.
        ## Todo: Find a better way to do this
        ##try:
        part_descriptor = getattr(library, catalog).descriptor(reference)
        self.form.Info.clear()
        for option in part_descriptor:
            self.form.Info.insertPlainText(
                "{} = {}\n".format(
                    option, part_descriptor[option]
                )
            )

        try:
            ok = self.is_available(catalog, reference)
        except KeyError:
            ok=False
            
        if ok:
            self.form.Status.setText("Component Available")
            self.form.Status.setStyleSheet("color: green")
        else:
            self.form.Status.setText("Component not Available")
            self.form.Status.setStyleSheet("color: red")

        #except:
        #    pass

    def accept(self):
        catalog = self.form.Catalog.currentText()
        reference = self.form.Reference.currentText()

        if self.is_available(catalog, reference):

            part_descriptor = getattr(library, catalog).descriptor(reference)
            comptype = part_descriptor["type"]
            glass_catalogs =  part_descriptor["glass_catalogs"].lower()
            
            X = self.form.Xpos.value()
            Y = self.form.Ypos.value()
            Z = self.form.Zpos.value()
            Xrot = self.form.Xrot.value()
            Yrot = self.form.Yrot.value()
            Zrot = self.form.Zrot.value()

            obj = None

            if comptype == "SphericalLens":
                mat = part_descriptor["material"]
                th = part_descriptor["thickness"]
                diam = 2.0 * part_descriptor["radius"]
                c1 = part_descriptor["curvature_s1"]
                c2 = part_descriptor["curvature_s2"]

                matcat = material.find_material(mat, exact=True, unalias=True)[0][0]

                if matcat not in glass_catalogs:
                    raise ValueError("Trying to use a wrong glass catalog"
                                     f" {matcat} not in {glass_catalogs}")
                                     
                obj = InsertSL(c1, c2, th, diam, "L", matcat, mat)

            if comptype == "CylindricalLens":
                mat = part_descriptor["material"]
                th = part_descriptor["thickness"]
                size = part_descriptor["size"]

                c1 = part_descriptor["curvature_s1"]
                c2 = part_descriptor["curvature_s2"]

                matcat = material.find_material(mat, exact=True, unalias=True)[0][0]

                if matcat not in glass_catalogs:
                    raise ValueError("Trying to use a wrong glass catalog"
                                     f" {matcat} not in {glass_catalogs}")
                

                obj = InsertCL(c1, c2, th, 2*size[1], 2*size[0], "L", matcat, mat)

            elif comptype == "Doublet":
                mat1 = part_descriptor["material_l1"]
                mat2 = part_descriptor["material_l2"]
                th1 = part_descriptor["thickness_l1"]
                th2 = part_descriptor["thickness_l2"]
                diam = 2.0 * part_descriptor["radius"]
                c1 = part_descriptor["curvature_s1"]
                c2 = part_descriptor["curvature_s2"]
                c3 = part_descriptor["curvature_s3"]
                matcat1 = material.find_material(mat1, exact=True, unalias=True)[0][0]
                matcat2 = material.find_material(mat2, exact=True, unalias=True)[0][0]

                if matcat1 not in glass_catalogs:
                    raise ValueError("Trying to use a wrong glass catalog"
                                     f" {matcat1} not in {glass_catalogs}")
                if matcat2 not in glass_catalogs:
                    raise ValueError("Trying to use a wrong glass catalog"
                                     f" {matcat2} not in {glass_catalogs}")
                
                obj = InsertDL(
                    c1,
                    c2,
                    th1,
                    c2,
                    c3,
                    th2,
                    diam,
                    0,
                    "L",
                    matcat1,
                    mat1,
                    matcat2,
                    mat2,
                )

            elif comptype == "AirSpacedDoublet":
                mat1 = part_descriptor["material_l1"]
                mat2 = part_descriptor["material_l2"]
                th1 = part_descriptor["thickness_l1"]
                th2 = part_descriptor["thickness_l2"]
                airgap = part_descriptor["air_gap"]

                diam = 2.0 * part_descriptor["radius"]
                c1 = part_descriptor["curvature_s1"]
                c2 = part_descriptor["curvature_s2"]
                c3 = part_descriptor["curvature_s3"]
                c4 = part_descriptor["curvature_s4"]
                matcat1 = material.find_material(mat1, exact=True, unalias=True)[0][0]
                matcat2 = material.find_material(mat2, exact=True, unalias=True)[0][0]

                if matcat1 not in glass_catalogs:
                    raise ValueError("Trying to use a wrong glass catalog"
                                     f" {matcat1} not in {glass_catalogs}")
                if matcat2 not in glass_catalogs:
                    raise ValueError("Trying to use a wrong glass catalog"
                                     f" {matcat2} not in {glass_catalogs}")
                                     
                obj = InsertDL(
                    c1,
                    c2,
                    th1,
                    c3,
                    c4,
                    th2,
                    diam,
                    airgap,
                    "L",
                    matcat1,
                    mat1,
                    matcat2,
                    mat2,
                )

            if obj is not None:
                m = FreeCAD.Matrix()
                m.rotateX(radians(Xrot))
                m.rotateY(radians(Yrot))
                m.rotateZ(radians(Zrot))
                m.move((X, Y, Z))
                p1 = FreeCAD.Placement(m)
                obj.Placement = p1
                obj.Reference = "{} - {}".format(catalog, reference)

            FreeCADGui.Control.closeDialog()


class CatalogComponentMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, CatalogComponentGUI)

    def GetResources(self):
        return {
            "MenuText": "Catalog Component",
            # "Accel": "Ctrl+M",
            "ToolTip": "Catalog Component",
            "Pixmap": "",
        }
