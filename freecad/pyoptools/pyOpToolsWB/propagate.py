# -*- coding: utf-8 -*-
import FreeCAD, Part

from math import radians
from .wbcommand import *
from .pyoptoolshelpers import getActiveSystem
from .feedback import FeedbackHelper

from pyoptools.raytrace.system import System

from pyoptools.misc.pmisc.misc import wavelength2RGB
from pyoptools.raytrace.calc import parallel_propagate


class PropagateMenu:
    def __init__(self):
        # Esta no tiene GUI, no necesitamos heredar de WBCommandMenu
        # WBCommandMenu.__init__(self,None)
        pass

    def GetResources(self):
        from freecad.pyoptools import ICONPATH
        import os
        
        # Base tooltip
        tooltip = "Propagate rays through optical system (Alt+P)"
        
        # Add disabled reason if not active
        if not self.IsActive():
            if FreeCAD.ActiveDocument is None:
                tooltip += " - Disabled: No document open"
            else:
                tooltip += " - Disabled: No ray sources in document"
        
        return {
            "MenuText": "Propagate",
            "Accel": "Alt+P",
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "propagate.svg"),
        }

    def IsActive(self):
        """
        Enable button only when a document is open and contains ray sources.
        
        Returns:
            bool: True if document exists with ray sources, False otherwise
        """
        if FreeCAD.ActiveDocument == None:
            return False
        
        # Check if any ray sources exist (RaysPoint, RaysPar, RaysArray, Ray)
        objs = FreeCAD.ActiveDocument.Objects
        ray_sources = [
            obj for obj in objs 
            if hasattr(obj, "ComponentType") and obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]
        ]
        
        return len(ray_sources) > 0

    def Activated(self):
        try:
            myObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "PROP")
            PropagatePart(myObj)
            myObj.ViewObject.Proxy = 0

            FreeCAD.ActiveDocument.recompute()
        except Exception as e:
            FeedbackHelper.show_error_dialog(
                "Ray Propagation Failed",
                FeedbackHelper.format_error(
                    e,
                    "Could not propagate rays through the optical system.\n\n"
                    "Please ensure:\n"
                    "• Light sources exist in the document\n"
                    "• Optical components are properly configured\n"
                    "• All components have valid parameters"
                )
            )


def get_prop_shape(ray):
    P1 = FreeCAD.Base.Vector(tuple(ray.origin))
    if len(ray.childs) > 0:
        P2 = FreeCAD.Base.Vector(tuple(ray.childs[0].origin))
    else:
        P2 = FreeCAD.Base.Vector(tuple(ray.origin + 10.0 * ray.direction))

    if ray.intensity != 0:
        L1 = [Part.makeLine(P1, P2)]
        for i in ray.childs:
            L1 = L1 + get_prop_shape(i)
    else:
        L1 = []
    return L1


class PropagatePart(WBPart):
    def __init__(self, obj):
        WBPart.__init__(self, obj, "Propagation")

        try:
            self.S, rays = getActiveSystem()
            self.S.ray_add(rays)
            self.S.propagate()
        except Exception as e:
            FeedbackHelper.show_error_dialog(
                "Ray Propagation Initialization Failed",
                FeedbackHelper.format_error(
                    e,
                    "Could not initialize ray propagation.\n\n"
                    "Please verify:\n"
                    "• The optical system contains valid components\n"
                    "• Ray sources have valid parameters\n"
                    "• No components have conflicting configurations"
                )
            )
            raise  # Re-raise so FreeCAD knows object creation failed

    @FeedbackHelper.with_busy_cursor
    def execute(self, obj):
        raydict = {}
        raylist = []
        colorlist = []

        # The System attribute ('S') is not being serialized correctly when saving
        # and reloading the model, causing it to be missing. As a workaround,
        # we skip plotting rays if 'S' is not present.
        if hasattr(self, "S"):
            try:
                for ray in self.S.prop_ray:
                    llines = get_prop_shape(ray)
                    wl = ray.wavelength
                    raydict[wl] = llines + raydict.get(wl, [])
                    raylist = raylist + llines
                    r, g, b = wavelength2RGB(wl)
                    colorlist = colorlist + [(r, g, b, 0.0)] * len(llines)
                
                lines = Part.makeCompound(raylist)
                obj.Shape = lines
                obj.ViewObject.LineColorArray = colorlist
                
                # Success feedback with ray count
                num_rays = len(self.S.prop_ray)
                FeedbackHelper.show_success(f"Ray propagation complete - {num_rays} rays traced")
                
            except Exception as e:
                FeedbackHelper.show_error_dialog(
                    "Ray Display Failed",
                    FeedbackHelper.format_error(
                        e,
                        "Ray propagation completed, but could not display rays.\n\n"
                        "The optical system may be too complex or contain invalid ray paths."
                    )
                )
                
        obj.ViewObject.Proxy = (
            0  # this is mandatory unless we code the ViewProvider too
        )

    def pyoptools_repr(self, obj):
        # Solo para que no se estrelle
        return []
