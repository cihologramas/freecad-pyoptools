from wbcommand import *
from pyoptools.misc.pmisc.misc import wavelength2RGB
import pyoptools.raytrace.ray.ray_source as rs_lib

class RaysParallelGUI(WBCommandGUI):
    def __init__(self):
        WBCommandGUI.__init__(self, 'RaysParallel.ui')

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
        enabled = self.form.Enabled.isChecked()

        D = self.form.D.value()
        m=FreeCAD.Matrix()

        #m.rotateX(radians(Ox))
        #m.rotateY(radians(Oy))
        #m.rotateZ(radians(Oz))

        m.move((X,Y,Z))
        obj=InsertRPar(nr,na, distribution,wavelenght,D,axis,"S",enabled)

        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()

class RaysParallelMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, RaysParallelGUI)

    def GetResources(self):
        return {"MenuText": "Add Parallel Ray Source",
                #"Accel": "Ctrl+M",
                "ToolTip": "Add Parallel Ray Source",
                "Pixmap": ""}





class RaysParPart(WBPart):
    def __init__(self,obj,nr=6,na=6,distribution="polar",wavelenght=633, D=5,axis=FreeCAD.Vector((0,0,1)),enabled=True):
        WBPart.__init__(self,obj,"RaysPar")

        obj.addProperty("App::PropertyInteger","nr")
        obj.addProperty("App::PropertyInteger","na")
        obj.addProperty("App::PropertyString","distribution")
        obj.addProperty("App::PropertyFloat","wavelenght")
        obj.addProperty("App::PropertyFloat","D")
        obj.addProperty("App::PropertyVector","axis")
        obj.addProperty("App::PropertyBool","enabled")

        obj.nr=nr
        obj.na=na
        obj.distribution=distribution.lower()
        obj.wavelenght = wavelenght
        obj.D = D
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


    def pyoptools_repr(self,obj):
        X,Y,Z = obj.Placement.Base
        dist=obj.distribution
        nr=obj.nr
        na=obj.na
        wl=obj.wavelenght
        R=obj.D/2.
        DX,DY,DZ=obj.axis
        r=[]
        if obj.enabled:
            if dist=="polar":
                r=rs_lib.parallel_beam_p(origin=(X,Y,Z),direction=(DX,DY,DZ),
                                         radius=R, num_rays=(nr,na),wavelength=wl/1000.,
                                         label="")

            elif dist=="cartesian":
                print "cartesian ray distribution, not implemented yet"
            elif dist=="random":
                print "random ray distribution, not implemented yet"
            else:
                print "Warning ray distribution {} not recognized".format(dist)

        return r


    def execute(self,obj):
        import Part,FreeCAD

        dist = obj.distribution.lower()


        if dist not in ["polar","cartesian"]:
            obj.distribution="polar"
            print "Ray Distribution not understood, changing it to polar"

        if dist == "polar":
            r=obj.D/2.
            d=Part.makeCylinder(r,5,FreeCAD.Vector(0,0,0),obj.axis)
            #d.translate(FreeCAD.Base.Vector(0,0,-0.5))
        else: #Cartesian
            #Todo: Crear una piramide en lugar de un cono
            d=Part.makeCone(0,10,10,dir)
            d.translate(FreeCAD.Base.Vector(0,0,-0.5))
        obj.Shape = d



def InsertRPar(nr=6, na=6,distribution="polar",wavelenght=633,D=5, axis =FreeCAD.Vector((0,0,1)),ID="S",enabled = True):
    import FreeCAD
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",ID)
    RaysParPart(myObj,nr,na,distribution,wavelenght,D,axis,enabled)
    myObj.ViewObject.Proxy = 0 # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj