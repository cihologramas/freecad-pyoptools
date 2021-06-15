#!/usr/bin/env python
"""Freecad macro used to adjust tilt of a mirror

Freecad macro for the pyoptools-workbench that adjusts the tilt of a mirror
(or other reflective element) until the reflected beam hits a given detector in
the center
"""

from pyOpToolsWB.pyoptoolshelpers import getActiveSystem
from numpy import dot
from scipy.optimize import minimize
from math import inf, degrees


def center_rot(drot, sen, el):
    """Auxiliar function to be used in an optimization algorithm
    
    drot: Vector with the 3 euler angles
    sen:  Sensor to be used to measure
    el: Element to be rotated

    After rotating the el component to the drot angles, the system is
    propagated, and the distance of the ray hit to the center of sen is
    returned.

    This function modifies the freecad system before obtaining the pyoptools
    system and as far as some small tests were made, is too slow. It is better
    to use the center_rot_pot()


    """
    myObj = FreeCAD.ActiveDocument.getObjectsByLabel(el)[0]

    base = myObj.Placement.Base
    rot = myObj.Placement.Rotation
    Rz, Ry, Rx = rot.toEuler()

    drx, dry, drz = drot

    new_pos = FreeCAD.Placement(base, FreeCAD.Rotation(Rz+drz, Ry+dry, Rx+drx))

    myObj.Placement = new_pos

    S, R = getActiveSystem()
    S.ray_add(R)
    S.propagate()
    myObj.Placement = FreeCAD.Placement(base, rot)
    hit = S[sen][0].hit_list[0][0]
    print(hit, drot)
    return dot(hit, hit)**.5


def center_rot_pot(drot, S, sen, el):
    """Auxiliar function to be used in an optimization algorithm that receives

    drot: Vector with the 3 euler angles
    S: pyoptools system
    sen:  Label of the sensor to be used to measure the ray_hit
    el: Label of the element to be rotated

    After rotating the el component to the drot angles, the system is
    propagated, and the distance of the ray hit to the center of sen is
    returned.

    This function uses only pyoptools, and is much faster than center_rot()


    """
    S.reset()
    C, P, D = S.complist[el]

    S.complist[el] = C, P, drot
    S.ray_add(R)
    S.propagate()

    hl = S[sen][0].hit_list

    if hl:
        hit = hl[0][0]
    else:
        hit = inf
    print( dot(hit, hit)**.5,hit, drot)
    return dot(hit, hit)**.5


S, R = getActiveSystem()

C, P, D = S["M1002"]


DR = minimize(center_rot_pot, D, (S, "SEN001", "M1002"), method="TNC")

print(DR)

DR=DR.x

myObj = FreeCAD.ActiveDocument.getObjectsByLabel("M1002")[0]

base = myObj.Placement.Base
rot = myObj.Placement.Rotation
print("***", D)
print("***", DR)
print(degrees(DR[0]),degrees(DR[1]),degrees(DR[2]))
newrot = FreeCAD.Rotation(degrees(DR[2]),degrees(DR[1]),degrees(DR[0]))

print(rot.toEuler())
print(newrot.toEuler())

new_pos = FreeCAD.Placement(base, newrot)

myObj.Placement = new_pos
