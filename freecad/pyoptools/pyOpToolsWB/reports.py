# -*- coding: utf-8 -*-
import FreeCAD
from .pyopPlot import *

#TODO: Plot no esta funcionando en Freecad 18 ni 19. Se inhabilita 

from .propagate import PropagatePart

class ReportsMenu:
    def __init__(self):
        #Esta no tiene GUI, no necesitamos heredar de WBCommandMenu
        #WBCommandMenu.__init__(self,None)
        pass

    def GetResources(self):
        return {"MenuText": "Reports",
                #"Accel": "Ctrl+M",
                "ToolTip": "Generate reports",
                "Pixmap": ""}

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
            return False
        else:
            return True

    def Activated(self):
        objs = FreeCAD.ActiveDocument.Objects


        #Eliminar los grupos y los rayos
        opobjs = list(filter(lambda x:hasattr(x,"ComponentType"),objs))

        #Buscar los sensores
        a_sensors = list(filter(lambda x: x.ComponentType=="Sensor",opobjs))

        #Mirar cuales estan activos

        sensors = list(filter(lambda x:x.Enabled, a_sensors))


        #Sacar los labels de los sensores
        slabels = list(map(lambda x:x.Label,sensors))

        #Buscar las propagaciones
        props = list(filter(lambda x: x.ComponentType=="Propagation",opobjs))

        #Sacar los sistemas opticos de las propagaciones
        ss = list(map(lambda x: x.Proxy.S, props))
        
        for s in ss:
            for n in slabels:
                ccd = s[n][0]
                hl=ccd.hit_list
                X=[]
                Y=[]
                if len(hl) >0:
                    for i in hl:
                        p=i[0]
                        # Hitlist[1] points to the incident ray
                        #col=wavelength2RGB(i[1].wavelength)
                        X.append(p[0])
                        Y.append(p[1])
                        #COL.append(col)
                fig=figure()
                fig.axes.plot(X,Y,"o")
                fig.axes.axis("equal")
                fig.axes.set_title(n)
                fig.update()
