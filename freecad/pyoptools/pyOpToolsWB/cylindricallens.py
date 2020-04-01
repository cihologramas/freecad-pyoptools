# -*- coding: utf-8 -*-
from .wbcommand import *

import Part

import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from math import radians


class CylindricalLensGUI(WBCommandGUI):
    def __init__(self):

        WBCommandGUI.__init__(self,'CylindricalLens.ui')

        self.form.Catalog.addItem("Value",[])
        for i in matlib.material.liblist:
            self.form.Catalog.addItem(i[0],sorted(i[1].keys()))

        self.form.Catalog.currentIndexChanged.connect(self.catalogChange)

    def catalogChange(self,*args):
        if args[0] == 0:
            self.form.Value.setEnabled(True)
        else:
            self.form.Value.setEnabled(False)


        while self.form.Reference.count():
            self.form.Reference.removeItem(0)
        self.form.Reference.addItems(self.form.Catalog.itemData(args[0]))

    def accept(self):
        CS1=self.form.CS1.value()
        CS2=self.form.CS2.value()
        CT=self.form.CT.value()
        W=self.form.W.value()
        H=self.form.H.value()
        X=self.form.Xpos.value()
        Y=self.form.Ypos.value()
        Z=self.form.Zpos.value()
        Xrot=self.form.Xrot.value()
        Yrot=self.form.Yrot.value()
        Zrot=self.form.Zrot.value()
        matcat=self.form.Catalog.currentText()
        if matcat=="Value":
            matref=str(self.form.Value.value())
        else:
            matref=self.form.Reference.currentText()

        obj=InsertCL(CS1,CS2,CT,W,H,ID="L",matcat=matcat,matref=matref)
        m=FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X,Y,Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()

class CylindricalLensMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, CylindricalLensGUI)

    def GetResources(self):
        return {"MenuText": "Cylindrical Lens",
                #"Accel": "Ctrl+M",
                "ToolTip": "Add Cylindrical Lens",
                "Pixmap": ""}

class CylindricalLensPart(WBPart):
    def __init__(self,obj,CS1=0.01,CS2=-0.01,CT=10,W=20,H=20, matcat="", matref=""):
        WBPart.__init__(self,obj,"SphericalLens")

        #Todo: Mirar como se puede usar un quantity
        obj.addProperty("App::PropertyPrecision","CS1","Shape","Curvature surface 1").CS1=(0,-10,10,1e-3)
        obj.addProperty("App::PropertyPrecision","CS2","Shape","Curvature surface 2").CS2=(0,-10,10,1e-3)

        obj.addProperty("App::PropertyLength","Thk","Shape","Lens center thickness")
        obj.addProperty("App::PropertyLength","H","Shape","Lens height")
        obj.addProperty("App::PropertyLength","W","Shape","Lens width")
        obj.addProperty("App::PropertyString","matcat","Material","Material catalog")
        obj.addProperty("App::PropertyString","matref","Material","Material reference")
        obj.CS1=CS1
        obj.CS2=CS2
        obj.Thk=CT
        obj.H=H
        obj.W=W
        obj.matcat=matcat
        obj.matref=matref
        obj.ViewObject.Transparency = 50

        obj.ViewObject.ShapeColor = (1.,1.,0.,0.)

    def execute(self,obj):

        obj.Shape = buildcylens(obj.CS1,obj.CS2,obj.W.Value,obj.H.Value,obj.Thk.Value)

    def pyoptools_repr(self,obj):
        thickness=obj.Thk.Value
        h=obj.H.Value
        w=obj.W.Value
        curvature_s1=obj.CS1
        curvature_s2=obj.CS2
        matcat=obj.matcat
        matref=obj.matref
        if matcat=="Value":
            material=float(matref.replace(",","."))
        else:
            material=getattr(matlib.material,matcat)[matref]

        return comp_lib.CylindricalLens(size=(h,w), thickness=thickness,
                                  curvature_s1=curvature_s1, curvature_s2=curvature_s2,
                                  material = material)


def InsertCL(CS1=0.01,CS2=-0.01,CT=10,W=20,H=20,ID="L",matcat="",matref=""):
    import FreeCAD
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",ID)
    CylindricalLensPart(myObj,CS1,CS2,CT,W,H,matcat,matref)
    myObj.ViewObject.Proxy = 0 # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj

def buildcylens(CS1,CS2,W,H,CT):

    d=Part.makeBox(H,W,CT+H)
    d.translate(FreeCAD.Base.Vector(-H/2.,-W/2,-(CT+H)/2))

    if CS1==0:
        R1=1e6
    else:
        R1=1./CS1

    f1=Part.makeCylinder(abs(R1),W,FreeCAD.Base.Vector(0,-W/2,0),
                         FreeCAD.Base.Vector(0,1,0))
    f1.translate(FreeCAD.Base.Vector(0,0,R1-CT/2))

    if CS2 ==0:
        R2 = 1e6
    else:
        R2=1./CS2

    f2=Part.makeCylinder(abs(R2),W,FreeCAD.Base.Vector(0,-W/2,0),
                         FreeCAD.Base.Vector(0,1,0))
    f2.translate(FreeCAD.Base.Vector(0,0,R2+CT/2))

    if R1>0:
        t=d.common(f1)
    else:
        t=d.cut(f1)
    if R2>0:
        t=t.cut(f2)
    else:
        t=t.common(f2)

    return t
