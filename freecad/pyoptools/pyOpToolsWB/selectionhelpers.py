# -*- coding: utf-8 -*-
"""Helper classes for 3D view selection in pyOpTools workbench.

Provides reusable SelectionObserver for picking objects from FreeCAD 3D view.
"""

import FreeCAD
import FreeCADGui
from .qthelpers import outputDialog


class SelectionObserver:
    """Observer for picking objects from 3D view with validation.
    
    Generic, reusable observer that can be used by any command needing
    to pick objects from the 3D view with custom validation logic.
    
    Supports both full object selection and sub-element selection (edges, faces, etc.).
    
    Usage example:
        # For full object selection:
        observer = SelectionObserver(
            callback=self.onObjectPicked,
            filter_func=lambda obj, sub: hasattr(obj, "Shape"),
            error_message="Please select an object with a shape"
        )
        FreeCADGui.Selection.addObserver(observer)
        
        # For sub-element (edge) selection:
        observer = SelectionObserver(
            callback=self.onEdgePicked,
            filter_func=lambda obj, sub: sub.startswith("Edge"),
            error_message="Please select an edge"
        )
        FreeCADGui.Selection.addObserver(observer)
    """
    
    def __init__(self, callback, filter_func, error_message):
        """Initialize observer with callback and validation.
        
        Args:
            callback: Function(obj, sub) called when valid selection made
                     - obj: FreeCAD object reference
                     - sub: Sub-element string (e.g., "Edge1", "" for full object)
            filter_func: Function(obj, sub) -> bool to validate selection
            error_message: String shown when invalid selection made
        """
        self.callback = callback
        self.filter_func = filter_func
        self.error_message = error_message
    
    def addSelection(self, doc, obj, sub, pnt):
        """Called when user selects object in 3D view.
        
        CRITICAL: obj is a STRING (object name), not the object itself!
        
        Args:
            doc: Document name (string)
            obj: Object name (string, NOT object reference!)
            sub: Sub-element name (string, e.g., "Edge1", "Face2", "")
            pnt: Point coordinates (tuple)
        """
        # Get object reference (obj is string name, not object!)
        obj_ref = FreeCAD.getDocument(doc).getObject(obj)
        
        # Validate selection (filter receives both obj and sub)
        if self.filter_func(obj_ref, sub):
            # Valid selection - call callback with obj and sub
            self.callback(obj_ref, sub)
            FreeCADGui.Selection.removeObserver(self)
        else:
            # Invalid selection - show error, keep observer active
            outputDialog(self.error_message)
    
    def removeSelection(self, doc, obj, sub):
        """Required observer method (not used)."""
        pass
    
    def setSelection(self, doc):
        """Required observer method (not used)."""
        pass
    
    def clearSelection(self, doc):
        """Required observer method (not used)."""
        pass
