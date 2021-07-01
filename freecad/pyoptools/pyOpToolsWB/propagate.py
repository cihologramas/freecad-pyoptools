# -*- coding: utf-8 -*-
import FreeCAD, Part

from math import radians
from .wbcommand import *
from .pyoptoolshelpers import getActiveSystem

from pyoptools.raytrace.system import System

from pyoptools.misc.pmisc.misc import wavelength2RGB
from pyoptools.raytrace.calc import parallel_propagate


class PropagateMenu:
    def __init__(self):
        #Esta no tiene GUI, no necesitamos heredar de WBCommandMenu
        #WBCommandMenu.__init__(self,None)
        pass

    def GetResources(self):
        return {"MenuText": "Propagate",
                #"Accel": "Ctrl+M",
                "ToolTip": "Propagate Rays",
                "Pixmap": ""}

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
            return False
        else:
            return True

    def Activated(self):

        myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","PROP")
        PP=PropagatePart(myObj)
        myObj.ViewObject.Proxy = 0


        doc=FreeCAD.activeDocument()

        PropagatePart(myObj)
        FreeCAD.ActiveDocument.recompute()


def get_prop_shape(ray):
    P1 = FreeCAD.Base.Vector(tuple(ray.pos))
    if len(ray.childs)>0:
        P2=FreeCAD.Base.Vector(tuple(ray.childs[0].pos))
    else:
        P2 = FreeCAD.Base.Vector(tuple(ray.pos + 10. * ray.dir))

    if ray.intensity!=0:
        L1 = [Part.makeLine(P1,P2)]
        for i in ray.childs:
            L1=L1+get_prop_shape(i)
    else:
        L1=[]
    return L1



class PropagatePart(WBPart):
    def __init__(self, obj):

        WBPart.__init__(self,obj,"Propagation")


        self.S,rays = getActiveSystem()
        self.S.ray_add(rays)
        self.S.propagate()

    def execute(self,obj):
        raydict={}
        raylist=[]
        colorlist=[]
        for ray in self.S.prop_ray:
            llines = get_prop_shape(ray)
            wl=ray.wavelength
            raydict[wl]=llines+raydict.get(wl,[])
            raylist=raylist+llines
            r,g,b = wavelength2RGB(wl)
            colorlist=colorlist+[(r,g,b,0.)]*len(llines)
        lines = Part.makeCompound(raylist)
        obj.Shape = lines
        obj.ViewObject.LineColorArray=colorlist
        obj.ViewObject.Proxy = 0 # this is mandatory unless we code the ViewProvider too

    def pyoptools_repr(self,obj):
        # Solo para que no se estrelle
        return []
