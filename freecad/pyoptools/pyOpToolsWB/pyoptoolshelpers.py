# -*- coding: utf-8 -*-
import FreeCAD
from pyoptools.raytrace.system import System
from freecad.pyoptools.pyOpToolsWB.qthelpers import outputDialog
from math import radians, degrees, cos, atan2, asin, pi
from numpy.linalg import inv
import pyoptools.raytrace.mat_lib as matlib


def getObjectPyOptoolsPose(obj):
    """Return position (X, Y, Z) and rotation (Rx, Ry, Rz) in radians from a FreeCAD object.

    Returns a tuple compatible with pyoptools system representation:
    ((X, Y, Z), (Rx, Ry, Rz))

    The rotation matrix decomposition idea was taken from:
    http://eecs.qmul.ac.uk/~gslabaugh/publications/euler.pdf
    and adjusted to the matrix rotation order of pyoptools.
    """
    pla = obj.getGlobalPlacement()
    X, Y, Z = pla.Base
    rotmat = pla.Rotation.toMatrix()

    RMA31 = rotmat.A31

    # Sometimes because of numerical approximations RMA31 can be
    # bigger than 1 ie. 1.0000000000000002
    if RMA31 > 1:
        RMA31 = 1.0
    if RMA31 < -1:
        RMA31 = -1.0

    Ry = -asin(RMA31)
    Cy = cos(Ry)

    # Anything bigger than 0.999999999 will be taken as 1. to avoid
    # numerical errors in the calculation of the angles.
    # Must check if there is a better way to solve this problem
    if abs(RMA31) < 0.999999999:
        Rx = atan2(rotmat.A32 / Cy, rotmat.A33 / Cy)
        Rz = atan2(rotmat.A21 / Cy, rotmat.A11 / Cy)
    else:
        Rz = 0
        # Check for sign instead of RMA31 == -1 equality
        if RMA31 < 0:
            Ry = pi / 2.0
            Rx = atan2(rotmat.A12, rotmat.A13)
        else:  # RMA31 == 1 branch
            Ry = -pi / 2.0
            Rx = atan2(-rotmat.A12, -rotmat.A13)

    return ((X, Y, Z), (Rx, Ry, Rz))


def getActiveSystem():
    """Return the pyoptools optical system representation.

    Function that converts the representation of the optical system
    drawn in FreeCAD, to an optical system in pyoptools.
    """
    objs = FreeCAD.ActiveDocument.Objects
    rays = []
    complist = []

    for obj in objs:
        # All pyoptools components have a ComponentType attribute.
        if not hasattr(obj, "ComponentType"):
            print(
                "Object {} not recognized by pyoptools, ignored.".format(
                    obj.Label
                )
            )
            continue
        if not obj.Enabled:
            continue

        print("Object {} recognized by pyoptools".format(obj.Label))

        (X, Y, Z), (Rx, Ry, Rz) = getObjectPyOptoolsPose(obj)

        
        # Hay que buscar una mejor forma de hacer esto, es decir como no tener
        # que pasar obj en los parametros
        try:
            e = obj.Proxy.pyoptools_repr(obj)
        except AttributeError:
            outputDialog(
                "Object {} can not be read. Check if the conversion\n"
                "file is correct. Type {}".format(obj.Label, obj.ComponentType)
            )

        if isinstance(e, list):
            rays.extend(e)
        else:
            complist.append(
                (
                    e,
                    (X, Y, Z),
                    (Rx, Ry, Rz),
                    obj.Label,
                )
            )

    S = System(complist)

    return S, rays

def getMaterial(matcat, matref):
    """Returns a pyoptools valid material instance, 
    """

    if matcat == "Value":
        material = float(matref.replace(",", "."))
    elif matcat == "aliases":
        material = matlib.material[matref]
    else:
        material = getattr(matlib.material, matcat)[matref]

    return material

