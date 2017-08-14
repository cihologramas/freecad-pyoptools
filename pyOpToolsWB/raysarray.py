# -*- coding: utf-8 -*-
from wbcommand import *
from pyoptools.misc.pmisc.misc import wavelength2RGB
import pyoptools.raytrace.ray.ray_source as rs_lib
from math import tan, radians
from numpy import linspace,dot,array,cos,sin


def rot_mat(r):
    c=cos(r)
    s=sin(r)

    rx=array([[1. , 0., 0.],
              [0. , c[0],-s[0]],
              [0. , s[0], c[0]]])

    ry=array([[ c[1], 0., s[1]],
              [ 0., 1., 0.],
              [-s[1], 0., c[1]]])


    rz=array([[ c[2],-s[2], 0.],
              [ s[2], c[2], 0.],
              [ 0., 0., 1.]])
    tm=dot(rz,dot(ry,rx))
    return tm

def rot_mat_i(r):

    c=cos(r)
    s=sin(r)

    rx=array([[ 1., 0., 0.],
              [ 0., c[0], s[0]],
              [ 0.,-s[0], c[0]]])

    ry=array([[ c[1], 0.,-s[1]],
              [ 0., 1., 0.],
              [ s[1], 0., c[1]]])


    rz=array([[ c[2], s[2], 0.],
              [-s[2], c[2], 0.],
              [ 0., 0., 1.]])

    return dot(rx,dot(ry,rz))




class RaysArrayGUI(WBCommandGUI):
    def __init__(self):
        WBCommandGUI.__init__(self, 'RaysArray.ui')

    def accept(self):

        X=self.form.Ox.value()
        Y=self.form.Oy.value()
        Z=self.form.Oz.value()

        Ox = self.form.Xrot.value()
        Oy = self.form.Yrot.value()
        Oz = self.form.Zrot.value()


        Sx = self.form.SX.value()
        Sy = self.form.SX.value()

        Nx = self.form.NX.value()
        Ny = self.form.NX.value()

        nr = self.form.nr.value()
        na = self.form.na.value()
        distribution = self.form.RayDistribution.currentText()
        wavelenght = self.form.wavelenght.value()
        enabled = self.form.Enabled.isChecked()

        angle = self.form.ang.value()

        m=FreeCAD.Matrix()

        m.rotateX(radians(Ox))
        m.rotateY(radians(Oy))
        m.rotateZ(radians(Oz))

        m.move((X,Y,Z))

        obj=InsertRArray(Sx,Sy,Nx,Ny, nr,na, angle, distribution,wavelenght,"S",enabled)

        p1 = FreeCAD.Placement(m)
        obj.Placement = p1
        FreeCADGui.Control.closeDialog()

class RaysArrayMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, RaysArrayGUI)

    def GetResources(self):
        return {"MenuText": "Add Array of Sources",
                #"Accel": "Ctrl+M",
                "ToolTip": "Add Array of Sources",
                "Pixmap": ""}





class RaysArrayPart(WBPart):
    def __init__(self,obj,Sx = 5,Sy = 5,Nx = 5 ,Ny= 5,nr=6,na=6,angle=10,distribution="polar",wavelenght=633,enabled=True):
        WBPart.__init__(self,obj,"RaysArray",enabled)

        obj.addProperty("App::PropertyInteger","nr").nr = nr
        obj.addProperty("App::PropertyInteger","na").na = na
        obj.addProperty("App::PropertyFloat","angle").angle = angle
        obj.addProperty("App::PropertyString","distribution").distribution = distribution
        obj.addProperty("App::PropertyFloat","wavelenght").wavelenght = wavelenght
        obj.addProperty("App::PropertyFloat","xSize").xSize = Sx
        obj.addProperty("App::PropertyFloat","ySize").ySize = Sy
        obj.addProperty("App::PropertyInteger","Nx").Nx = Nx
        obj.addProperty("App::PropertyInteger","Ny").Ny = Ny
        r,g,b = wavelength2RGB(wavelenght/1000.)

        obj.ViewObject.ShapeColor = (r,g,b,0.)


    def propertyChanged(self, obj, prop):

        # To keep all the housekeeping that WBPart do, this method replaces
        # the standard onChanged

        if prop == "wavelenght":
            r,g,b = wavelength2RGB(obj.wavelenght/1000.)
            obj.ViewObject.ShapeColor = (r,g,b,0.)



    def pyoptools_repr(self,obj):
        X,Y,Z = obj.Placement.Base
        dist=obj.distribution.lower()
        nr=obj.nr
        na=obj.na
        ang = obj.angle
        wl=obj.wavelenght
        RZ,RY,RX = obj.Placement.Rotation.toEuler()
        rm = rot_mat((radians(RX),radians(RY),radians(RZ)))
        dire=((radians(RX),radians(RY),radians(RZ)))

        r=[]
        if obj.enabled:
            if dist=="polar":
                for x in linspace(-obj.xSize/2,obj.xSize/2,obj.Nx):
                    for y in linspace(-obj.ySize/2,obj.ySize/2,obj.Ny):
                        xr,yr,zr =dot(rm,array((x,y,0),dtype="float64"))
                        r=r+rs_lib.point_source_p(origin=(X+xr,Y+yr,Z+zr),direction=dire,span=radians(ang),
                                      num_rays=(nr,na),wavelength=wl/1000., label="")

            elif dist=="cartesian":
                for x in linspace(-obj.xSize/2,obj.xSize/2,obj.Nx):
                    for y in linspace(-obj.ySize/2,obj.ySize/2,obj.Ny):
                        xr,yr,zr =dot(rm,array((x,y,0),dtype="float64"))
                        r=r+rs_lib.point_source_c(origin=(X+xr,Y+yr,Z+zr),direction=dire,span=(radians(ang),radians(ang))\
                                                  ,num_rays=(nr,na),wavelength=wl/1000., label="")
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
            r=5*tan(radians(obj.angle))
            d=[]
            for x in linspace(-obj.xSize/2,obj.xSize/2,obj.Nx):
                for y in linspace(-obj.ySize/2,obj.ySize/2,obj.Ny):
                    d.append(Part.makeCone(0,r,5,FreeCAD.Vector(x,y,0)))
        else: #Todo: Cambiar cono a piramide
            r=5*tan(radians(obj.angle))
            d = []
            for x in linspace(-obj.xSize/2,obj.xSize/2,obj.Nx):
                for y in linspace(-obj.ySize/2,obj.ySize/2,obj.Ny):
                    d.append(Part.makeCone(0,r,5,FreeCAD.Vector(x,y,0)))


        obj.Shape = Part.makeCompound(d)




def InsertRArray(Sx=5,Sy=5,Nx=5,Ny=5, nr =10,na=10, angle=5, distribution="polar",wavelenght=633,ID = "S",enabled = True):
    import FreeCAD
    myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",ID)
    RaysArrayPart(myObj,Sx,Sy,Nx,Ny,nr,na,angle,distribution,wavelenght,enabled)
    myObj.ViewObject.Proxy = 0 # this is mandatory unless we code the ViewProvider too
    FreeCAD.ActiveDocument.recompute()
    return myObj