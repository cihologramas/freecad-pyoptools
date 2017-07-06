from wbcommand import *
from pyoptools.misc.pmisc.misc import wavelength2RGB
import pyoptools.raytrace.ray.ray_source as rs_lib
from math import tan, radians

class RaysPointGUI(WBCommandGUI):
    def __init__(self):
        WBCommandGUI.__init__(self, 'RaysPoint.ui')

    def accept(self):

        X=self.form.Ox.value()
        Y=self.form.Oy.value()
        Z=self.form.Oz.value()

        Dx = self.form.Dx.value()
        Dy = self.form.Dy.value()
        Dz = self.form.Dz.value()

        axis = FreeCAD.Vector(Dx,Dy,Dz)

        nr = self.form.nr.value()
        na = self.form.na.value()
        distribution = self.form.RayDistribution.currentText()
        wavelenght = self.form.wavelenght.value()
        angle = self.form.ang.value()
        enabled = self.form.Enabled.isChecked()
        m=FreeCAD.Matrix()
        #m.rotateX(radians(Ox))
        #m.rotateY(radians(Oy))
        #m.rotateZ(radians(Oz))

        m.move((X,Y,Z))
        obj=InsertRPoint(nr,na, distribution,wavelenght,angle,axis,"S",enabled)

        p1 = FreeCAD.Placement(m)
        obj.Placement = p1

        FreeCADGui.Control.closeDialog()

class RaysPointMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self,RaysPointGUI)

    def GetResources(self):
        return {"MenuText": "Add Point Source",
                #"Accel": "Ctrl+M",
                "ToolTip": "Add Point Source",
                "Pixmap": ""}


class RaysPointPart(WBPart):
    def __init__(self,obj,nr=6,na=6,distribution="polar",wavelenght=633, angle=30,axis=FreeCAD.Vector((0,0,1)),enabled = True):
        WBPart.__init__(self,obj,"RaysPoint")
        obj.Proxy = self
        obj.addProperty("App::PropertyInteger","nr")
        obj.addProperty("App::PropertyInteger","na")
        obj.addProperty("App::PropertyString","distribution")
        obj.addProperty("App::PropertyFloat","wavelenght")
        obj.addProperty("App::PropertyFloat","angle")
        obj.addProperty("App::PropertyVector","axis")
        obj.addProperty("App::PropertyBool","enabled")

        obj.nr=nr
        obj.na=na
        obj.distribution=distribution.lower()
        obj.wavelenght = wavelenght
        obj.angle = angle
        obj.axis = axis
        obj.enabled=enabled
        r,g,b = wavelength2RGB(wavelenght/1000.)
        obj.ViewObject.ShapeColor = (r,g,b,0.)



    def onChanged(self, obj, prop):
        if prop =="cType":
            obj.setEditorMode("cType", 2)

        if prop == "wavelenght":
            r,g,b = wavelength2RGB(obj.wavelenght/1000.)
            obj.ViewObject.ShapeColor = (r,g,b,0.)


    def execute(self,obj):
        import Part,FreeCAD

        dist = obj.distribution.lower()


        if dist not in ["polar","cartesian"]:
            obj.distribution="polar"
            print "Ray Distribution not understood, changing it to polar"

        if dist == "polar":
            r=5*tan(radians(obj.angle))
            d=Part.makeCone(0,r,5,FreeCAD.Vector(0,0,0),obj.axis)
            #d.translate(FreeCAD.Base.Vector(0,0,-0.5))
        else: #Cartesian
            #Todo: Crear una piramide en lugar de un cono
            d=Part.makeCone(0,10,10,dir)
            d.translate(FreeCAD.Base.Vector(0,0,-0.5))
        obj.Shape = d

    def pyoptools_repr(self,obj):
        dist=obj.distribution
        nr=obj.nr
        na=obj.na
        wl=obj.wavelenght
        ang=obj.angle
        DX,DY,DZ=obj.axis
        X,Y,Z = obj.Placement.Base
        r=[]
        if obj.enabled:
            if dist=="polar":
                r=rs_lib.point_source_p(origin=(X,Y,Z),direction=(DX,DY,DZ),span=radians(ang),
                                          num_rays=(nr,na),wavelength=wl/1000., label="")
            elif dist=="cartesian":
                print "cartesian ray distribution, not implemented yet"
            elif dist=="random":
                print "random ray distribution, not implemented yet"
            else:
                print "Warning ray distribution {} not recognized".format(dist)

        return r



def InsertRPoint(nr=6, na=6,distribution="polar",wavelenght=633,angle=30, axis =FreeCAD.Vector((0,0,1)),ID="S", enabled = True):
    import FreeCAD
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",ID)
    RaysPointPart(myObj,nr,na,distribution,wavelenght,angle,axis,enabled)
    myObj.ViewObject.Proxy = 0 # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj

