# -*- coding: utf-8 -*-
"""Position mirror at intersection of two rays (ray lines or ray sources) with normal as bisector."""

import FreeCAD
import FreeCADGui
import Part
from math import sqrt
from PySide import QtCore, QtGui, QtWidgets

from .wbcommand import WBCommandGUI, WBCommandMenu
from .feedback import FeedbackHelper
from .qthelpers import outputDialog
from .selectionhelpers import SelectionObserver


class PositionMirrorOn2RaysGUI(WBCommandGUI):
    """GUI for positioning mirror at intersection of two rays."""
    
    def __init__(self):
        """Initialize UI and state."""
        WBCommandGUI.__init__(self, "PositionMirrorOn2Rays.ui")
        
        # State tracking
        self.ray1_obj = None           # Selected object containing ray 1
        self.ray1_edge = None          # Selected edge for ray 1
        self.ray2_obj = None           # Selected object containing ray 2
        self.ray2_edge = None          # Selected edge for ray 2
        self.mirror = None             # Selected mirror to position
        self.original_placement = None # For Cancel/restore
        
        # Selection observers
        self.ray1_observer = None
        self.ray2_observer = None
        self.mirror_observer = None
        
        # Populate mirror dropdown
        self._populateMirrorDropdown()
        
        # Connect signals for real-time preview
        self.form.invertRay1.stateChanged.connect(self.updatePreview)
        self.form.invertRay2.stateChanged.connect(self.updatePreview)
        self.form.invertNormal.stateChanged.connect(self.updatePreview)
        self.form.mirrorComboBox.currentIndexChanged.connect(self.onMirrorDropdownChanged)
        
        # Setup pick buttons
        self._setupPickButton(
            self.form.pickRay1Button,
            self.startRay1Pick,
            "Click to select first ray (line from propagation or ray source) from 3D view"
        )
        self._setupPickButton(
            self.form.pickRay2Button,
            self.startRay2Pick,
            "Click to select second ray (line from propagation or ray source) from 3D view"
        )
        self._setupPickButton(
            self.form.pickMirrorButton,
            self.startMirrorPick,
            "Click to select mirror from 3D view"
        )
        
        # Setup Apply/Close button icons
        self._setupButtonIcons()
        
        # Connect Apply/Close buttons
        self.form.applyButton.clicked.connect(self.onApplyClicked)
        self.form.closeButton.clicked.connect(self.reject)
    
    def _populateMirrorDropdown(self):
        """Populate mirror dropdown with mirror components."""
        import FreeCAD
        
        # Add empty/placeholder item at top
        self.form.mirrorComboBox.addItem("(Select Mirror)", None)
        
        objs = FreeCAD.ActiveDocument.Objects
        opobjs = filter(lambda x: hasattr(x, "ComponentType"), objs)
        
        for obj in opobjs:
            # Only include mirrors
            if obj.ComponentType in ["RoundMirror", "RectangularMirror"]:
                self.form.mirrorComboBox.addItem(obj.Label, obj)
        
        # Start with placeholder selected (index 0)
        self.form.mirrorComboBox.setCurrentIndex(0)
    
    def _setupPickButton(self, button, slot, tooltip):
        """Configure pick button with icon and connections."""
        button.setToolTip(tooltip)
        button.clicked.connect(slot)
        
        # Set icon matching PositionOnRay style
        try:
            from freecad.pyoptools import ICONPATH
            import os
            
            icon_path = os.path.join(ICONPATH, "pick-from-view.svg")
            if os.path.exists(icon_path):
                icon = QtGui.QIcon(icon_path)
                button.setIcon(icon)
                button.setIconSize(QtCore.QSize(16, 16))
        except:
            # Fallback to theme icon
            try:
                icon = QtGui.QIcon.fromTheme("edit-select")
                if not icon.isNull():
                    button.setIcon(icon)
            except:
                pass
    
    def _setupButtonIcons(self):
        """Setup icons for Apply and Close buttons to match PositionOnRay style."""
        try:
            from freecad.pyoptools import ICONPATH
            import os
            
            # Apply button icon
            icon_path = os.path.join(ICONPATH, "dialog-ok-apply.svg")
            if os.path.exists(icon_path):
                icon = QtGui.QIcon(icon_path)
                self.form.applyButton.setIcon(icon)
            else:
                # Fallback to theme icon
                apply_icon = QtGui.QIcon.fromTheme("dialog-ok-apply")
                if not apply_icon.isNull():
                    self.form.applyButton.setIcon(apply_icon)
            
            # Close button icon
            icon_path = os.path.join(ICONPATH, "window-close.svg")
            if os.path.exists(icon_path):
                icon = QtGui.QIcon(icon_path)
                self.form.closeButton.setIcon(icon)
            else:
                # Fallback to theme icon
                close_icon = QtGui.QIcon.fromTheme("dialog-close")
                if not close_icon.isNull():
                    self.form.closeButton.setIcon(close_icon)
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Could not load button icons: {e}\n")
    
    # === Ray 1 Picking Methods ===

    def _getRayWidgets(self, ray_index):
        """Return (label, p1_label, p2_label) widgets for the given ray index (1 or 2)."""
        if ray_index == 1:
            return self.form.ray1Label, self.form.ray1P1Label, self.form.ray1P2Label
        return self.form.ray2Label, self.form.ray2P1Label, self.form.ray2P2Label

    def _setRayState(self, ray_index, obj, edge):
        """Set internal state for the given ray index (1 or 2)."""
        if ray_index == 1:
            self.ray1_obj = obj
            self.ray1_edge = edge
        else:
            self.ray2_obj = obj
            self.ray2_edge = edge

    def _getRayObserver(self, ray_index):
        return self.ray1_observer if ray_index == 1 else self.ray2_observer

    def _setRayObserver(self, ray_index, observer):
        if ray_index == 1:
            self.ray1_observer = observer
        else:
            self.ray2_observer = observer

    def _startRayPick(self, ray_index):
        """Start pick mode for ray selection (ray_index = 1 or 2)."""
        import FreeCAD
        import FreeCADGui

        # If already picking, toggle off
        if self._getRayObserver(ray_index) is not None:
            self._stopRayPick(ray_index)
            return

        # Stop other picks if active
        if ray_index == 1:
            if self.ray2_observer is not None:
                self.stopRay2Pick()
        else:
            if self.ray1_observer is not None:
                self.stopRay1Pick()
        if self.mirror_observer is not None:
            self.stopMirrorPick()

        # Create and register observer
        observer = SelectionObserver(
            callback=(lambda obj, sub: self._onRayPicked(ray_index, obj, sub)),
            filter_func=self.isPartLine,
            error_message="Please select a ray line (from propagation) or a ray source (RaysPoint, RaysPar, Ray, etc.)"
        )
        self._setRayObserver(ray_index, observer)
        FreeCADGui.Selection.addObserver(observer)

        # Visual feedback
        which = "first" if ray_index == 1 else "second"
        FreeCAD.Console.PrintMessage(f"Click on {which} ray (line or ray source) in 3D view\n")

        # Change cursor to crosshair
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)

    def _stopRayPick(self, ray_index):
        """Stop pick mode for ray selection (ray_index = 1 or 2)."""
        import FreeCADGui

        observer = self._getRayObserver(ray_index)
        if observer is not None:
            FreeCADGui.Selection.removeObserver(observer)
            self._setRayObserver(ray_index, None)

        # Restore normal cursor
        QtGui.QApplication.restoreOverrideCursor()

    def _onRayPicked(self, ray_index, obj, sub):
        """Handle a picked ray (ray source or line edge) for ray_index = 1 or 2."""
        import FreeCAD
        import Part

        label_w, p1_w, p2_w = self._getRayWidgets(ray_index)

        # Check if this is a ray source or a line
        if hasattr(obj, "ComponentType") and obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]:
            # This is a ray source - store the object
            self._setRayState(ray_index, obj, None)  # No edge for ray sources

            # Get position and direction from placement
            pla = obj.Placement
            pos = pla.Base
            direction = pla.Rotation.multVec(FreeCAD.Vector(0, 0, 1))

            # Update UI labels
            label_w.setText(f"{obj.Label} (Ray Source)")
            label_w.setStyleSheet("")  # Remove gray/italic
            p1_w.setText(f"Origin: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")
            p2_w.setText(f"Direction: ({direction.x:.3f}, {direction.y:.3f}, {direction.z:.3f})")
        else:
            # This is a line edge
            # Extract the specific edge from the object
            if not sub or not hasattr(obj.Shape, 'getElement'):
                FreeCAD.Console.PrintError(f"Cannot get edge from {obj.Label}, sub={sub}\n")
                return

            try:
                edge = obj.Shape.getElement(sub)
            except:
                FreeCAD.Console.PrintError(f"Failed to get element {sub} from {obj.Label}\n")
                return

            if not isinstance(edge, Part.Edge):
                FreeCAD.Console.PrintError(f"Selected element is not an edge: {type(edge)}\n")
                return

            # Store both the parent object and the edge
            self._setRayState(ray_index, obj, edge)

            # Extract endpoints from the edge
            p1 = edge.Vertexes[0].Point
            p2 = edge.Vertexes[1].Point

            # Update UI labels
            label_w.setText(f"{obj.Label} ({sub})")
            label_w.setStyleSheet("")  # Remove gray/italic
            p1_w.setText(f"P1: ({p1.x:.2f}, {p1.y:.2f}, {p1.z:.2f})")
            p2_w.setText(f"P2: ({p2.x:.2f}, {p2.y:.2f}, {p2.z:.2f})")

        # Cleanup
        self._stopRayPick(ray_index)

        # Update preview and status
        self.updatePreview()
        self.updateStatus()
    
    def startRay1Pick(self):
        """Start pick mode for ray 1 selection."""
        self._startRayPick(1)
    
    def stopRay1Pick(self):
        """Stop pick mode for ray 1 selection."""
        self._stopRayPick(1)
    
    def onRay1Picked(self, obj, sub):
        """Called when valid ray 1 picked."""
        self._onRayPicked(1, obj, sub)
    
    # === Ray 2 Picking Methods ===
    
    def startRay2Pick(self):
        """Start pick mode for ray 2 selection."""
        self._startRayPick(2)
    
    def stopRay2Pick(self):
        """Stop pick mode for ray 2 selection."""
        self._stopRayPick(2)
    
    def onRay2Picked(self, obj, sub):
        """Called when valid ray 2 picked."""
        self._onRayPicked(2, obj, sub)
    
    def isPartLine(self, obj, sub):
        """Validate selected element is a straight line edge or ray source.
        
        Args:
            obj: FreeCAD object to check
            sub: Sub-element (only used for line edges)
            
        Returns:
            bool: True if object is a line edge or ray source
        """
        if obj is None:
            return False
        
        # Check if it's a ray source
        if hasattr(obj, "ComponentType") and obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]:
            return True
        
        # Check if it's a line edge
        # Must have a Shape with edges
        if not hasattr(obj, "Shape") or not hasattr(obj.Shape, "Edges"):
            return False
        
        # sub should be like "Edge1", "Edge2", etc.
        if not sub or not sub.startswith("Edge"):
            return False
        
        try:
            # Try to get the specific edge
            edge = obj.Shape.getElement(sub)
            if not isinstance(edge, Part.Edge):
                return False
            
            # Check if it's a straight line
            if not hasattr(edge, "Curve"):
                return False
            
            return isinstance(edge.Curve, Part.Line)
        except:
            return False
    
    # === Mirror Picking Methods ===
    
    def startMirrorPick(self):
        """Start pick mode for mirror selection."""
        import FreeCAD
        import FreeCADGui
        
        # If already picking, toggle off
        if self.mirror_observer is not None:
            self.stopMirrorPick()
            return
        
        # Stop other picks if active
        if self.ray1_observer is not None:
            self.stopRay1Pick()
        if self.ray2_observer is not None:
            self.stopRay2Pick()
        
        # Create and register observer
        self.mirror_observer = SelectionObserver(
            callback=self.onMirrorPicked,
            filter_func=self.isMirror,
            error_message="Please select a mirror component (RoundMirror or RectangularMirror)"
        )
        FreeCADGui.Selection.addObserver(self.mirror_observer)
        
        # Visual feedback
        FreeCAD.Console.PrintMessage("Click on mirror in 3D view\n")
        
        # Change cursor to crosshair
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)
    
    def stopMirrorPick(self):
        """Stop pick mode for mirror selection."""
        import FreeCADGui
        
        if self.mirror_observer is not None:
            FreeCADGui.Selection.removeObserver(self.mirror_observer)
            self.mirror_observer = None
        
        # Restore normal cursor
        QtGui.QApplication.restoreOverrideCursor()
    
    def onMirrorPicked(self, obj, sub):
        """Called when valid mirror picked."""
        # Find in dropdown and select
        for i in range(self.form.mirrorComboBox.count()):
            if self.form.mirrorComboBox.itemData(i) == obj:
                self.form.mirrorComboBox.setCurrentIndex(i)
                break
        
        # Cleanup
        self.stopMirrorPick()
    
    def onMirrorDropdownChanged(self, index):
        """Called when mirror dropdown changes."""
        if index < 0:
            return
        
        # IMPORTANT: Restore previous mirror's placement before switching
        if self.mirror is not None and self.original_placement is not None:
            self.mirror.Placement = self.original_placement
            import FreeCAD
            FreeCAD.ActiveDocument.recompute()
        
        # Get newly selected mirror (may be None for placeholder)
        self.mirror = self.form.mirrorComboBox.itemData(index)
        
        # Store original placement for new mirror (only if valid mirror)
        if self.mirror is not None:
            self.original_placement = self.mirror.Placement
        else:
            # Placeholder selected - clear mirror
            self.original_placement = None
        
        # Update preview with new mirror
        self.updatePreview()
        self.updateStatus()
    
    def isMirror(self, obj, sub):
        """Validate object is a mirror component."""
        if obj is None:
            return False
        
        if not hasattr(obj, "ComponentType"):
            return False
        
        # Only accept mirrors
        return obj.ComponentType in ["RoundMirror", "RectangularMirror"]
    
    # === Geometric Calculations ===
    
    def getRayData(self, ray_obj, ray_edge):
        """Extract position and direction from ray source or line edge.
        
        Args:
            ray_obj: FreeCAD object (ray source or object containing edge)
            ray_edge: Edge object (or None for ray sources)
            
        Returns:
            tuple: (origin_point, direction_vector) or (None, None) if invalid
        """
        import FreeCAD
        
        if ray_obj is None:
            return None, None
        
        # Check if it's a ray source
        if hasattr(ray_obj, "ComponentType") and ray_obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]:
            # Extract from ray source placement
            pla = ray_obj.Placement
            origin = pla.Base
            direction = pla.Rotation.multVec(FreeCAD.Vector(0, 0, 1))
            direction.normalize()
            return origin, direction
        
        # Otherwise it's a line edge
        if ray_edge is None:
            return None, None
        
        # Extract from edge endpoints
        p1 = ray_edge.Vertexes[0].Point
        p2 = ray_edge.Vertexes[1].Point
        direction = (p2 - p1).normalize()
        
        # Use p1 as origin for line edges
        return p1, direction
    
    def findIntersection(self, origin1, dir1, origin2, dir2):
        """Find intersection point of two rays.
        
        Args:
            origin1: Origin point of first ray
            dir1: Direction vector of first ray (normalized)
            origin2: Origin point of second ray
            dir2: Direction vector of second ray (normalized)
            
        Returns:
            tuple: (intersection_point, distance_between_lines) or (None, distance)
                   If rays don't intersect exactly, returns closest point and distance
        """
        import FreeCAD
        
        if origin1 is None or origin2 is None or dir1 is None or dir2 is None:
            return None, float('inf')
        
        # Check if rays are parallel
        cross = dir1.cross(dir2)
        if cross.Length < 1e-6:
            # Rays are parallel - return None
            return None, float('inf')
        
        # Find closest points on two lines using parametric equations
        # Line 1: P1 = origin1 + t1 * dir1
        # Line 2: P2 = origin2 + t2 * dir2
        # We want to minimize |P1 - P2|
        
        w0 = origin1 - origin2
        a = dir1.dot(dir1)  # always 1 for normalized
        b = dir1.dot(dir2)
        c = dir2.dot(dir2)  # always 1 for normalized
        d = dir1.dot(w0)
        e = dir2.dot(w0)
        
        denom = a * c - b * b
        if abs(denom) < 1e-10:
            # Shouldn't happen if not parallel, but safety check
            return None, float('inf')
        
        t1 = (b * e - c * d) / denom
        t2 = (a * e - b * d) / denom
        
        # Calculate closest points on each line
        closest_p1 = origin1 + dir1 * t1
        closest_p2 = origin2 + dir2 * t2
        
        # Calculate distance between closest points
        distance = (closest_p2 - closest_p1).Length
        
        # Use midpoint as intersection
        intersection = FreeCAD.Vector(
            (closest_p1.x + closest_p2.x) / 2.0,
            (closest_p1.y + closest_p2.y) / 2.0,
            (closest_p1.z + closest_p2.z) / 2.0
        )
        
        return intersection, distance
    
    def calculateBisector(self, origin1, dir1, origin2, dir2, intersection, invert_ray1=False, invert_ray2=False):
        """Calculate bisector direction from two rays.
        
        The mirror normal is calculated as d1 - d2 (subtraction).
        Use the invert checkboxes to flip ray directions when needed.
        
        Args:
            origin1: Origin point of first ray
            dir1: Direction vector of first ray (normalized)
            origin2: Origin point of second ray
            dir2: Direction vector of second ray (normalized)
            intersection: Intersection point (for direction calculation)
            invert_ray1: If True, use -dir1 in calculations
            invert_ray2: If True, use -dir2 in calculations
            
        Returns:
            FreeCAD.Vector: Normalized bisector direction
        """
        import FreeCAD
        
        if origin1 is None or origin2 is None or dir1 is None or dir2 is None:
            return FreeCAD.Vector(0, 0, 1)
        
        # Make copies to avoid modifying the original vectors
        d1 = FreeCAD.Vector(dir1)
        d2 = FreeCAD.Vector(dir2)
        
        # Apply manual inversion flags
        if invert_ray1:
            d1 = -d1
        if invert_ray2:
            d2 = -d2
        
        # Calculate bisector as d1 - d2
        bisector = d1 - d2
        
        # Normalize the bisector
        if bisector.Length > 1e-6:
            bisector.normalize()
        else:
            # Rays are parallel - use perpendicular
            bisector = FreeCAD.Vector(0, 0, 1)
        
        return bisector
    
    def computeMirrorPlacement(self):
        """Compute mirror placement at intersection with bisector normal.
        
        Returns:
            FreeCAD.Placement: New placement, or None if inputs invalid
        """
        if self.ray1_obj is None or self.ray2_obj is None or self.mirror is None:
            return None
        
        import FreeCAD
        
        # Get ray data (origin and direction) for both rays
        origin1, dir1 = self.getRayData(self.ray1_obj, self.ray1_edge)
        origin2, dir2 = self.getRayData(self.ray2_obj, self.ray2_edge)
        
        if origin1 is None or origin2 is None:
            return None
        
        # Get invert flags from UI
        invert_ray1 = self.form.invertRay1.isChecked()
        invert_ray2 = self.form.invertRay2.isChecked()
        
        # Find intersection point
        intersection, distance = self.findIntersection(origin1, dir1, origin2, dir2)
        
        if intersection is None:
            return None
        
        # Calculate bisector direction with invert flags
        bisector = self.calculateBisector(origin1, dir1, origin2, dir2, intersection, invert_ray1, invert_ray2)
        
        # Check if we need to invert
        if self.form.invertNormal.isChecked():
            bisector = -bisector
        
        # Create rotation to align Z-axis with bisector
        z_axis = FreeCAD.Vector(0, 0, 1)
        rotation = FreeCAD.Rotation(z_axis, bisector)
        
        # Create and return new placement
        return FreeCAD.Placement(intersection, rotation), distance
    
    # === Preview and Apply ===
    
    def updateStatus(self):
        """Update status label with current state."""
        if self.ray1_obj is None or self.ray2_obj is None:
            self.form.statusLabel.setText("")
            return
        
        # Get ray data
        origin1, dir1 = self.getRayData(self.ray1_obj, self.ray1_edge)
        origin2, dir2 = self.getRayData(self.ray2_obj, self.ray2_edge)
        
        if origin1 is None or origin2 is None:
            self.form.statusLabel.setText("")
            return
        
        # Check if rays intersect
        intersection, distance = self.findIntersection(origin1, dir1, origin2, dir2)
        
        if intersection is None:
            self.form.statusLabel.setText("⚠️ Warning: Rays are parallel and do not intersect")
            self.form.statusLabel.setStyleSheet(
                "padding: 5px; background-color: #fff3cd; border-radius: 3px; color: #856404;"
            )
        elif distance > 0.1:  # Threshold for "close enough"
            self.form.statusLabel.setText(
                f"⚠️ Warning: Rays do not intersect exactly (distance: {distance:.3f} mm)\n"
                f"Using midpoint between closest points."
            )
            self.form.statusLabel.setStyleSheet(
                "padding: 5px; background-color: #fff3cd; border-radius: 3px; color: #856404;"
            )
        else:
            self.form.statusLabel.setText(
                f"✓ Rays intersect at: ({intersection.x:.2f}, {intersection.y:.2f}, {intersection.z:.2f})"
            )
            self.form.statusLabel.setStyleSheet(
                "padding: 5px; background-color: #d4edda; border-radius: 3px; color: #155724;"
            )
    
    def updatePreview(self):
        """Update mirror position in real-time (preview)."""
        if self.mirror is None:
            return
        
        try:
            # Compute new placement
            result = self.computeMirrorPlacement()
            
            if result is None:
                return
            
            new_placement, distance = result
            
            # Apply preview (without transaction)
            self.mirror.Placement = new_placement
            FreeCAD.ActiveDocument.recompute()
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Preview update failed: {e}\n")
    
    def onApplyClicked(self):
        """Apply button - commit transformation with transaction."""
        if self.mirror is None or self.ray1_obj is None or self.ray2_obj is None:
            outputDialog("Please select two rays and a mirror")
            return
        
        try:
            # Compute new placement
            result = self.computeMirrorPlacement()
            
            if result is None:
                outputDialog("Could not compute placement - rays may be parallel")
                return
            
            new_placement, distance = result
            
            # Check if rays are too far apart
            if distance > 1.0:  # 1mm threshold
                from PySide import QtGui
                reply = QtGui.QMessageBox.question(
                    None,
                    "Rays Don't Intersect",
                    f"The selected rays do not intersect exactly.\n"
                    f"Distance between rays: {distance:.3f} mm\n\n"
                    f"Continue anyway using midpoint?",
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                    QtGui.QMessageBox.No
                )
                if reply == QtGui.QMessageBox.No:
                    return
            
            # IMPORTANT: Restore original placement before transaction
            if self.original_placement is not None:
                self.mirror.Placement = self.original_placement
            
            # Apply with transaction (for undo support)
            FreeCAD.ActiveDocument.openTransaction("Position Mirror on 2 Rays")
            try:
                self.mirror.Placement = new_placement
                FreeCAD.ActiveDocument.recompute()
                FreeCAD.ActiveDocument.commitTransaction()
                
                FeedbackHelper.show_success(
                    f"Mirror '{self.mirror.Label}' positioned at ray intersection"
                )
                
                # Clear mirror selection (keep rays selected for next mirror)
                self.mirror = None
                self.original_placement = None
                self.form.mirrorComboBox.setCurrentIndex(0)
                
            except Exception as e:
                FreeCAD.ActiveDocument.abortTransaction()
                raise
                
        except Exception as e:
            FeedbackHelper.show_error_dialog(
                "Apply Failed",
                FeedbackHelper.format_error(e, "Could not apply transformation")
            )
    
    def reject(self):
        """Close/Cancel button - restore original placement."""
        import FreeCADGui
        from PySide import QtGui
        
        # Stop any active picking
        self.stopRay1Pick()
        self.stopRay2Pick()
        self.stopMirrorPick()
        
        # Check if mirror has unsaved preview changes
        has_unsaved_changes = (
            self.mirror is not None and 
            self.original_placement is not None and
            self.mirror.Placement != self.original_placement
        )
        
        if has_unsaved_changes:
            # Show confirmation dialog
            reply = QtGui.QMessageBox.question(
                None,
                "Unsaved Changes",
                f"Mirror '{self.mirror.Label}' has been moved but not applied.\n\n"
                "Do you want to apply the changes before closing?",
                QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel,
                QtGui.QMessageBox.Save  # Default button
            )
            
            if reply == QtGui.QMessageBox.Save:
                # Apply changes then close
                self.onApplyClicked()
                # onApplyClicked already clears mirror, so nothing to revert
                FreeCADGui.Control.closeDialog()
                return
            elif reply == QtGui.QMessageBox.Cancel:
                # Stay open, don't close
                return
            # else: Discard - continue to revert below
        
        # Restore original placement if mirror was modified (Discard case)
        if self.mirror is not None and self.original_placement is not None:
            self.mirror.Placement = self.original_placement
            FreeCAD.ActiveDocument.recompute()
        
        # Close dialog
        FreeCADGui.Control.closeDialog()
    
    def getStandardButtons(self):
        """Return no standard buttons - we have custom buttons in UI."""
        return 0


class PositionMirrorOn2RaysMenu(WBCommandMenu):
    """Menu command for Position Mirror on 2 Rays."""
    
    def __init__(self):
        WBCommandMenu.__init__(self, PositionMirrorOn2RaysGUI)
    
    def GetResources(self):
        """Return menu resources."""
        from freecad.pyoptools import ICONPATH
        import os
        
        tooltip = "Position mirror at intersection of two rays (ray lines or ray sources) with normal as bisector"
        
        if not self.IsActive():
            if not FreeCAD.ActiveDocument:
                tooltip += " - Disabled: No document open"
            else:
                tooltip += " - Disabled: No mirrors in document"
        
        return {
            "MenuText": "Position Mirror on 2 Rays",
            "Accel": "Shift+M",  # Keyboard shortcut
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "position-mirror-on-2-rays.svg"),
        }
    
    def IsActive(self):
        """Enable button only when mirrors exist."""
        if FreeCAD.ActiveDocument is None:
            return False
        
        # Check if any mirrors exist
        objs = FreeCAD.ActiveDocument.Objects
        mirrors = [
            obj for obj in objs
            if hasattr(obj, "ComponentType") 
            and obj.ComponentType in ["RoundMirror", "RectangularMirror"]
        ]
        
        return len(mirrors) > 0
