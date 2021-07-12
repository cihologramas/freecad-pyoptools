# -*- coding: utf-8 -*-
import FreeCAD
from pyoptools.raytrace.system import System
from freecad.pyoptools.pyOpToolsWB.qthelpers import outputDialog
from math import radians


def getActiveSystem():

    objs = FreeCAD.ActiveDocument.Objects
    rays = []
    complist = []

    for obj in objs:
        # Todos los componentes de pyoptools tienen attributo cType
        if not hasattr(obj, "cType"):
            print(
                "Object {} not recognized by pyoptools, ignored.".format(
                    obj.Label
                )
            )
            continue
        if not obj.enabled:
            continue

        print("Object {} recognized by pyoptools".format(obj.Label))

        pla = obj.getGlobalPlacement()
        X, Y, Z = pla.Base

        # No entiendo el orden pero parece que funciona
        RZ, RY, RX = pla.Rotation.toEuler()

        # Hay que buscar una mejor forma de hacer esto, es decir como no tener
        # que pasar obj en los parametros
        try:
            e = obj.Proxy.pyoptools_repr(obj)
        except AttributeError:
            outputDialog(
                "Object {} can not be read. Check if the conversion\n"
                "file is correct."
            )

        if isinstance(e, list):
            rays.extend(e)
        else:
            complist.append(
                (
                    e,
                    (X, Y, Z),
                    (radians(RX), radians(RY), radians(RZ)),
                    obj.Label,
                )
            )

    S = System(complist)

    return S, rays
