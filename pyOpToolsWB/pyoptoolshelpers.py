# -*- coding: utf-8 -*-
import FreeCAD
from pyoptools.raytrace.system import System
from math import radians

def getActiveSystem():

    objs = FreeCAD.ActiveDocument.Objects
    rays=[]
    complist=[]
    for obj in objs:
        if not obj.enabled:
            continue
        X,Y,Z = obj.Placement.Base
        #No entiendo el orden pero parece que funciona
        RZ,RY,RX = obj.Placement.Rotation.toEuler()

        # Hay que buscar una mejor forma de hacer esto, es decir como no tener
        # que pasar obj en los parametros
        e=obj.Proxy.pyoptools_repr(obj)
        if isinstance(e,list):
            rays.extend(e)
        else:
            complist.append((e,(X,Y,Z),(radians(RX),radians(RY),radians(RZ)),obj.Label))

    S=System(complist)

    return S,rays