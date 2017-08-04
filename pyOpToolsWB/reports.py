# -*- coding: utf-8 -*-
import FreeCAD, Plot
from propagate import PropagatePart

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
        opobjs = filter(lambda x:hasattr(x,"cType"),objs)

        #Buscar los sensores
        a_sensors = filter(lambda x: x.cType=="Sensor",opobjs)

        #Mirar cuales estan activos

        sensors =filter(lambda x:x.enabled, a_sensors)


        #Sacar los labels de los sensores
        slabels = map(lambda x:x.Label,sensors)

        #Buscar las propagaciones
        props = filter(lambda x: x.cType=="Propagation",opobjs)

        #Sacar los sistemas opticos de las propagaciones
        ss = map(lambda x: x.Proxy.S, props)


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
                fig=Plot.figure()
                fig.axes.plot(X,Y,"o")
                fig.axes.axis("equal")
                fig.update()