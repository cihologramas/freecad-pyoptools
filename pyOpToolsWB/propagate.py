# -*- coding: utf-8 -*-
import FreeCAD, Part

from math import radians
from wbcommand import *
from pyoptoolshelpers import getActiveSystem

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

        #Se agrupan los rayos para poder eliminarlos facil
        grp=doc.addObject("App::DocumentObjectGroup", "Rays")
        llines=[]

        #Crear un diccionario para agrupar los rayos por longitud de onda

        raydict={}

        for ray in PP.S.prop_ray:
            #lines = Part.Wire(get_prop_shape(ray))
            llines = get_prop_shape(ray)
            wl=ray.wavelength
            raydict[wl]=llines+raydict.get(wl,[])

        for wl in raydict.keys():
            lines = Part.makeCompound(raydict[wl])
            myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Ray")
            myObj.Shape=lines
            r,g,b = wavelength2RGB(wl)
            myObj.ViewObject.LineColor = (r,g,b,0.)
            myObj.ViewObject.Proxy = 0
            grp.addObject(myObj)

        FreeCAD.ActiveDocument.recompute()




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
        pass

    def pyoptools_repr(self,obj):
        # Solo para que no se estrelle
        return []