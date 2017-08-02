# -*- coding: utf-8 -*-
from wbcommand import *
import pyoptools.raytrace.comp_lib as comp_lib
import pyoptools.raytrace.mat_lib as matlib
from pyoptools.raytrace.system.idealcomponent import IdealThickLens
from pyoptools.raytrace.shape.circular import Circular
from math import radians


class ThickLensGUI(WBCommandGUI):
    def __init__(self):
        WBCommandGUI.__init__(self, 'IdealThickLens.ui')

    def accept(self):
        Th=self.form.Thk.value()
        D=self.form.D.value()

        PP1=self.form.PP1.value()
        PP2=self.form.PP2.value()

        showpp = self.form.ShowPP.isChecked()
        showft = self.form.ShowFRT.isChecked()
        f=self.form.f.value()


        X=self.form.Xpos.value()
        Y=self.form.Ypos.value()
        Z=self.form.Zpos.value()
        Xrot=self.form.Xrot.value()
        Yrot=self.form.Yrot.value()
        Zrot=self.form.Zrot.value()




        obj=InsertTL(Th,D,PP1,PP2,f,showpp,showft,ID="L")
        m=FreeCAD.Matrix()
        m.rotateX(radians(Xrot))
        m.rotateY(radians(Yrot))
        m.rotateZ(radians(Zrot))
        m.move((X,Y,Z))
        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()


class ThickLensMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self,ThickLensGUI)

    def GetResources(self):
        return {"MenuText": "Thick Lens",
                #"Accel": "Ctrl+M",
                "ToolTip": "Add Ideal Thick Lens",
                "Pixmap": ""}

class ThickLensPart(WBPart):
    def __init__(self,obj,Th=10,D=50,PP1=0,PP2=0,f=100,SPP=False,SFRT=False):

        WBPart.__init__(self,obj,"ThickLens")
        obj.Proxy = self
        obj.addProperty("App::PropertyLength","Thk","Shape",
                        "Lens Thickness (distance between entrance and exit surfaces in the lens)")
        obj.addProperty("App::PropertyLength","D","Shape","Lens diameter")
        obj.addProperty("App::PropertyDistance","PP1P","Shape","Principal plane 1 position")
        obj.addProperty("App::PropertyDistance","PP2P","Shape","Principal plane 2 position")
        obj.addProperty("App::PropertyDistance","f","Shape","lens Focal length")
        obj.addProperty("App::PropertyBool","SPP","Other","Show principal planes")
        obj.addProperty("App::PropertyBool","SFRT","Other","Show full ray trace")
        obj.Thk=Th
        obj.D=D
        obj.PP1P=PP1
        obj.PP2P=PP2
        obj.SPP=SPP
        obj.SFRT=SFRT
        obj.f=f

        obj.ViewObject.Transparency = 50
        obj.ViewObject.ShapeColor = (1.,0.,0.,0.)


    def pyoptools_repr(self,obj):

        return IdealThickLens(Circular(radius=obj.D.Value/2.), obj.Thk.Value,
                              (obj.PP1P.Value,obj.PP2P.Value),f=obj.f.Value,complete_trace=obj.SFRT)


    def execute(self,obj):
        import Part,FreeCAD

        d=Part.makeCylinder(obj.D.Value/2.,obj.Thk.Value,FreeCAD.Base.Vector(0,0,-obj.Thk.Value/2))
        p1=Part.makeCylinder(obj.D.Value/2.,0.01,FreeCAD.Base.Vector(0,0,obj.PP1P.Value-obj.Thk.Value/2))
        p2=Part.makeCylinder(obj.D.Value/2.,0.01,FreeCAD.Base.Vector(0,0,obj.Thk.Value/2+obj.PP2P.Value))

        if obj.SPP:
            obj.Shape = Part.makeCompound([d,p1,p2])
        else:
            obj.Shape = d

#(Th,D,PP1,PP2,showpp,showft,ID="L")
def InsertTL(Th=10,D=50,PP1=2,PP2=-2,f=100, SPP=False, SFRT=False, ID="L"):
    import FreeCAD
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",ID)
    ThickLensPart(myObj,Th,D,PP1,PP2,f,SPP,SFRT)
    myObj.ViewObject.Proxy = 0 # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj
