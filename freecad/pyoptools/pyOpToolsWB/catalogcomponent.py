# -*- coding: utf-8 -*-
"""Classes used to define a component from different catalogs."""
import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from PySide import QtGui
from pyoptools.raytrace.library import library
from pyoptools.raytrace.mat_lib.material import find_material
from .sphericallens import InsertSL
from .doubletlens import InsertDL
from math import radians


class CatalogComponentGUI(WBCommandGUI):
    def __init__(self):
        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "CatalogComponent.ui"])

        for lib in dir(library):
            c = getattr(library, lib)
            if isinstance(c, library.Library):
                self.form.Catalog.addItem(lib, sorted(c.parts()))

        self.catalogChange(0)
        self.referenceChange(0)

        self.form.Catalog.currentIndexChanged.connect(self.catalogChange)
        self.form.Reference.currentIndexChanged.connect(self.referenceChange)

    def catalogChange(self, *args):

        while self.form.Reference.count():
            self.form.Reference.removeItem(0)

        for reference in self.form.Catalog.itemData(args[0]):
            red = QtGui.QPixmap(16, 16)
            red.fill(QtGui.QColor("red"))
            green = QtGui.QPixmap(16, 16)
            green.fill(QtGui.QColor("green"))

            if self.is_available(self.form.Catalog.currentText(), reference):
                color = green
            else:
                color = red

            self.form.Reference.addItem(color, reference)
            # item.setStyleSheet("color: green")

    def is_available(self, catalog, reference):
        # catalog = self.form.Catalog.currentText()
        # reference = self.form.Reference.currentText()
        lib = getattr(library, catalog)
        ok = True
        comp_type = lib.parser.get(reference, "type")
        if comp_type == "SphericalLens":
            comp_mat = lib.parser.get(reference, "material")
            matlibs = find_material(comp_mat)
            if len(matlibs) == 0:
                print("material {} not found".format(comp_mat))
                ok = False

        elif comp_type in ["Doublet", "AirSpacedDoublet"]:
            comp_mat1 = lib.parser.get(reference, "material_l1")
            matlibs1 = find_material(comp_mat1)
            comp_mat2 = lib.parser.get(reference, "material_l2")
            matlibs2 = find_material(comp_mat2)

            if len(matlibs1) == 0:
                print("material {} not found".format(comp_mat1))
                ok = False
            if len(matlibs2) == 0:
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
        # To avoid some errors raised when there is a catalog change.
        # Todo: Find a better way to do this
        try:
            options = lib.parser.options(reference)

            self.form.Info.clear()
            for option in options:
                self.form.Info.insertPlainText(
                    "{} = {}\n".format(
                        option, lib.parser.get(reference, option)
                    )
                )

            ok = self.is_available(catalog, reference)
            if ok:
                self.form.Status.setText("Component Available")
                self.form.Status.setStyleSheet("color: green")
            else:
                self.form.Status.setText("Component not Available")
                self.form.Status.setStyleSheet("color: red")

        except:
            pass

    def accept(self):
        catalog = self.form.Catalog.currentText()
        reference = self.form.Reference.currentText()

        if self.is_available(catalog, reference):

            lib = getattr(library, catalog)
            comptype = lib.parser.get(reference, "type")
            X = self.form.Xpos.value()
            Y = self.form.Ypos.value()
            Z = self.form.Zpos.value()
            Xrot = self.form.Xrot.value()
            Yrot = self.form.Yrot.value()
            Zrot = self.form.Zrot.value()

            obj = None

            if comptype == "SphericalLens":
                mat = lib.parser.get(reference, "material")
                th = lib.parser.getfloat(reference, "thickness")
                diam = 2.0 * lib.parser.getfloat(reference, "radius")
                c1 = lib.parser.getfloat(reference, "curvature_s1")
                c2 = lib.parser.getfloat(reference, "curvature_s2")

                matcat = find_material(mat)[0]
                obj = InsertSL(c1, c2, th, diam, "L", matcat, mat)

            elif comptype == "Doublet":
                mat1 = lib.parser.get(reference, "material_l1")
                mat2 = lib.parser.get(reference, "material_l2")
                th1 = lib.parser.getfloat(reference, "thickness_l1")
                th2 = lib.parser.getfloat(reference, "thickness_l2")
                diam = 2.0 * lib.parser.getfloat(reference, "radius")
                c1 = lib.parser.getfloat(reference, "curvature_s1")
                c2 = lib.parser.getfloat(reference, "curvature_s2")
                c3 = lib.parser.getfloat(reference, "curvature_s3")
                matcat1 = find_material(mat1)[0]
                matcat2 = find_material(mat2)[0]
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
                mat1 = lib.parser.get(reference, "material_l1")
                mat2 = lib.parser.get(reference, "material_l2")
                th1 = lib.parser.getfloat(reference, "thickness_l1")
                th2 = lib.parser.getfloat(reference, "thickness_l2")
                airgap = lib.parser.getfloat(reference, "air_gap")

                diam = 2.0 * lib.parser.getfloat(reference, "radius")
                c1 = lib.parser.getfloat(reference, "curvature_s1")
                c2 = lib.parser.getfloat(reference, "curvature_s2")
                c3 = lib.parser.getfloat(reference, "curvature_s3")
                c4 = lib.parser.getfloat(reference, "curvature_s4")
                matcat1 = find_material(mat1)[0]
                matcat2 = find_material(mat2)[0]
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
