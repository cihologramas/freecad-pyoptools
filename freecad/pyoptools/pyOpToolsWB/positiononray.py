# -*- coding: utf-8 -*-
"""Position component origin along ray line with Z-axis alignment."""

import FreeCAD
import FreeCADGui
import Part
from math import degrees, radians
from PySide import QtCore, QtGui, QtWidgets

from .wbcommand import WBCommandGUI, WBCommandMenu
from .feedback import FeedbackHelper
from .qthelpers import outputDialog
from .selectionhelpers import SelectionObserver


class PositionOnRayGUI(WBCommandGUI):
    """GUI for positioning component along ray line."""
    
    def __init__(self):
        """Initialize UI and state."""
        WBCommandGUI.__init__(self, "PositionOnRay.ui")
        
        # State tracking
        self.line_obj = None           # Selected object containing the ray line
        self.selected_edge = None      # Selected edge (Part.Edge) from line_obj
        self.component = None           # Selected component to position
        self.original_placement = None  # For Cancel/restore
        self.line_observer = None       # SelectionObserver for line picking
        self.component_observer = None  # SelectionObserver for component picking
        
        # Populate component dropdown
        self._populateComponentDropdown()
        
        # Connect signals for real-time preview
        self.form.distanceInput.valueChanged.connect(self.updatePreview)
        self.form.invertDirection.stateChanged.connect(self.updatePreview)
        self.form.componentComboBox.currentIndexChanged.connect(self.onComponentDropdownChanged)
        
        # Setup pick buttons with icons
        self._setupPickButton(
            self.form.pickLineButton,
            self.startLinePick,
            "Click to select ray line from 3D view"
        )
        self._setupPickButton(
            self.form.pickComponentButton,
            self.startComponentPick,
            "Click to select component from 3D view"
        )
        
        # Setup Apply/Close button icons
        self._setupButtonIcons()
        
        # Connect Apply/Close buttons
        self.form.applyButton.clicked.connect(self.onApplyClicked)
        self.form.closeButton.clicked.connect(self.reject)
    
    def _populateComponentDropdown(self):
        """Populate component dropdown with optical components."""
        import FreeCAD
        
        # Add empty/placeholder item at top
        self.form.componentComboBox.addItem("(Select Component)", None)
        
        objs = FreeCAD.ActiveDocument.Objects
        opobjs = filter(lambda x: hasattr(x, "ComponentType"), objs)
        
        for obj in opobjs:
            # Exclude only propagation results (ray visualization)
            if obj.ComponentType not in ["Propagation"]:
                self.form.componentComboBox.addItem(obj.Label, obj)
        
        # Start with placeholder selected (index 0)
        self.form.componentComboBox.setCurrentIndex(0)
    
    def _setupPickButton(self, button, slot, tooltip):
        """Configure pick button with icon and tooltip.
        
        Args:
            button: QPushButton to configure
            slot: Function to connect to clicked signal
            tooltip: Tooltip text to display
        """
        from PySide import QtGui, QtCore
        import os
        
        # Connect signal
        button.clicked.connect(slot)
        
        # Set tooltip
        button.setToolTip(tooltip)
        
        # Load custom pick icon
        try:
            from freecad.pyoptools import ICONPATH
            
            icon_path = os.path.join(ICONPATH, "pick-from-view.svg")
            icon = QtGui.QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QtCore.QSize(16, 16))
        except Exception as e:
            # If icon loading fails, button will just show without icon
            import FreeCAD
            
            FreeCAD.Console.PrintLog(f"Could not load pick button icon: {e}\n")
    
    def _setupButtonIcons(self):
        """Setup icons for Apply and Close buttons."""
        from PySide import QtGui, QtCore
        import os
        
        try:
            from freecad.pyoptools import ICONPATH
            
            # Apply button - green checkmark icon
            if hasattr(self.form, "applyButton"):
                icon_path = os.path.join(ICONPATH, "dialog-ok-apply.svg")
                if os.path.exists(icon_path):
                    icon = QtGui.QIcon(icon_path)
                    self.form.applyButton.setIcon(icon)
                    self.form.applyButton.setIconSize(QtCore.QSize(16, 16))
            
            # Close button - red X icon
            if hasattr(self.form, "closeButton"):
                icon_path = os.path.join(ICONPATH, "window-close.svg")
                if os.path.exists(icon_path):
                    icon = QtGui.QIcon(icon_path)
                    self.form.closeButton.setIcon(icon)
                    self.form.closeButton.setIconSize(QtCore.QSize(16, 16))
        except Exception as e:
            import FreeCAD
            FreeCAD.Console.PrintLog(f"Could not load button icons: {e}\n")
    
    # === Line Picking Methods ===
    
    def startLinePick(self):
        """Start pick mode for line selection."""
        import FreeCAD
        import FreeCADGui
        
        # If already picking, toggle off
        if self.line_observer is not None:
            self.stopLinePick()
            return
        
        # Stop component pick if active
        if self.component_observer is not None:
            self.stopComponentPick()
        
        # Create and register observer
        self.line_observer = SelectionObserver(
            callback=self.onLinePicked,
            filter_func=self.isPartLine,
            error_message="Please select a line object (Part.makeLine from ray propagation)"
        )
        FreeCADGui.Selection.addObserver(self.line_observer)
        
        # Visual feedback
        self.form.pickLineButton.setDown(True)
        FreeCAD.Console.PrintMessage("Click on ray line in 3D view\n")
        
        # Change cursor to crosshair
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)
    
    def stopLinePick(self):
        """Stop pick mode for line selection."""
        import FreeCADGui
        
        if self.line_observer is not None:
            FreeCADGui.Selection.removeObserver(self.line_observer)
            self.line_observer = None
        
        # Reset button state
        if hasattr(self.form, "pickLineButton"):
            self.form.pickLineButton.setDown(False)
            self.form.pickLineButton.setChecked(False)
        
        # Restore normal cursor
        QtGui.QApplication.restoreOverrideCursor()
    
    def onLinePicked(self, obj, sub):
        """Called when valid line (edge) picked.
        
        Args:
            obj: FreeCAD object containing the edge
            sub: Sub-element string (e.g., "Edge1")
        """
        import FreeCAD
        import Part
        
        # Extract the specific edge from the object
        if not sub or not hasattr(obj.Shape, 'getElement'):
            FreeCAD.Console.PrintError(f"Cannot get edge from {obj.Label}, sub={sub}\n")
            return
        
        try:
            edge = obj.Shape.getElement(sub)  # Get the specific edge (e.g., "Edge1")
        except:
            FreeCAD.Console.PrintError(f"Failed to get element {sub} from {obj.Label}\n")
            return
        
        if not isinstance(edge, Part.Edge):
            FreeCAD.Console.PrintError(f"Selected element is not an edge: {type(edge)}\n")
            return
        
        # Store both the parent object and the edge
        self.line_obj = obj
        self.selected_edge = edge
        
        # Extract endpoints from the edge
        p1 = edge.Vertexes[0].Point
        p2 = edge.Vertexes[1].Point
        
        # Update UI labels
        self.form.rayLineLabel.setText(f"{obj.Label} ({sub})")
        self.form.p1Label.setText(f"P1: ({p1.x:.2f}, {p1.y:.2f}, {p1.z:.2f})")
        self.form.p2Label.setText(f"P2: ({p2.x:.2f}, {p2.y:.2f}, {p2.z:.2f})")
        
        # Cleanup
        self.stopLinePick()
        
        # Update preview if component already selected
        self.updatePreview()
    
    def isPartLine(self, obj, sub):
        """Validate selected element is a straight line edge.
        
        Args:
            obj: FreeCAD object
            sub: Sub-element string (e.g., "Edge1", "Edge2", etc.)
        
        Returns:
            bool: True if sub-element is a straight line edge
        """
        import FreeCAD
        import Part
        
        if obj is None:
            return False
        
        # Must have a sub-element (edge)
        if not sub or not sub.startswith("Edge"):
            return False
        
        # Get the specific edge
        if not hasattr(obj.Shape, 'getElement'):
            return False
        
        try:
            edge = obj.Shape.getElement(sub)
        except:
            return False
        
        # Check if it's an edge
        if not isinstance(edge, Part.Edge):
            return False
        
        # Check if edge has a Curve and if it's a straight line
        if not hasattr(edge, "Curve"):
            return False
        
        return isinstance(edge.Curve, Part.Line)
    
    # === Component Picking Methods ===
    
    def startComponentPick(self):
        """Start pick mode for component selection."""
        import FreeCAD
        import FreeCADGui
        
        # If already picking, toggle off
        if self.component_observer is not None:
            self.stopComponentPick()
            return
        
        # Stop line pick if active
        if self.line_observer is not None:
            self.stopLinePick()
        
        # Create and register observer
        self.component_observer = SelectionObserver(
            callback=self.onComponentPicked,
            filter_func=self.isOpticalComponent,
            error_message="Please select an optical component (not a ray source)"
        )
        FreeCADGui.Selection.addObserver(self.component_observer)
        
        # Visual feedback
        self.form.pickComponentButton.setDown(True)
        FreeCAD.Console.PrintMessage("Click on optical component in 3D view\n")
        
        # Change cursor to crosshair
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)
    
    def stopComponentPick(self):
        """Stop pick mode for component selection."""
        import FreeCADGui
        
        if self.component_observer is not None:
            FreeCADGui.Selection.removeObserver(self.component_observer)
            self.component_observer = None
        
        # Reset button state
        if hasattr(self.form, "pickComponentButton"):
            self.form.pickComponentButton.setDown(False)
            self.form.pickComponentButton.setChecked(False)
        
        # Restore normal cursor
        QtGui.QApplication.restoreOverrideCursor()
    
    def onComponentPicked(self, obj, sub):
        """Called when valid component picked.
        
        Args:
            obj: FreeCAD optical component object
            sub: Sub-element (ignored for component selection)
        """
        # Find in dropdown and select
        for i in range(self.form.componentComboBox.count()):
            if self.form.componentComboBox.itemData(i) == obj:
                self.form.componentComboBox.setCurrentIndex(i)
                break
        
        # Cleanup
        self.stopComponentPick()
    
    def onComponentDropdownChanged(self, index):
        """Called when component dropdown changes.
        
        Args:
            index: Dropdown index
        """
        if index < 0:
            return
        
        # IMPORTANT: Restore previous component's placement before switching
        if self.component is not None and self.original_placement is not None:
            self.component.Placement = self.original_placement
            import FreeCAD
            FreeCAD.ActiveDocument.recompute()
        
        # Get newly selected component (may be None for placeholder)
        self.component = self.form.componentComboBox.itemData(index)
        
        # Store original placement for new component (only if valid component)
        if self.component is not None:
            self.original_placement = self.component.Placement
        else:
            # Placeholder selected - clear component
            self.original_placement = None
        
        # Update preview with new component (will do nothing if component is None)
        self.updatePreview()
    
    def isOpticalComponent(self, obj, sub):
        """Validate object is optical component.
        
        Args:
            obj: FreeCAD object to check
            sub: Sub-element (ignored for component selection)
        
        Returns:
            bool: True if object is an optical component
        """
        if obj is None:
            return False
        
        if not hasattr(obj, "ComponentType"):
            return False
        
        # Exclude only propagation results (ray visualization)
        return obj.ComponentType not in ["Propagation"]
    
    # === Constraint Solver ===
    
    def computePlacementOnRay(self):
        """Compute component placement along ray line.
        
        Returns:
            FreeCAD.Placement: New placement, or None if inputs invalid
        """
        if self.selected_edge is None or self.component is None:
            return None
        
        import FreeCAD
        
        # Extract endpoints from the selected edge
        p1 = self.selected_edge.Vertexes[0].Point
        p2 = self.selected_edge.Vertexes[1].Point
        
        # Get inputs
        distance = self.form.distanceInput.value()
        invert = self.form.invertDirection.isChecked()
        
        # Determine ray start/end based on invert
        if invert:
            ray_start = p2
            ray_end = p1
        else:
            ray_start = p1
            ray_end = p2
        
        # Calculate ray direction (unit vector)
        ray_direction = (ray_end - ray_start)
        ray_direction.normalize()
        
        # Calculate new position
        new_position = ray_start + (ray_direction * distance)
        
        # Calculate rotation to align Z-axis with ray
        z_axis = FreeCAD.Vector(0, 0, 1)
        rotation = FreeCAD.Rotation(z_axis, ray_direction)
        
        # Create and return new placement
        return FreeCAD.Placement(new_position, rotation)
    
    # === Preview and Apply ===
    
    def updatePreview(self):
        """Update component position in real-time (preview)."""
        if self.component is None or self.selected_edge is None:
            return
        
        try:
            # Compute new placement
            new_placement = self.computePlacementOnRay()
            
            if new_placement is not None:
                # Update component (real-time preview)
                self.component.Placement = new_placement
                FreeCAD.ActiveDocument.recompute()
        except Exception as e:
            # Silently ignore errors during preview
            FreeCAD.Console.PrintWarning(f"Preview update failed: {e}\n")
    
    def onApplyClicked(self):
        """Apply button - commit transformation with transaction."""
        if self.component is None or self.line_obj is None:
            outputDialog("Please select both a ray line and a component")
            return
        
        try:
            # Compute new placement
            new_placement = self.computePlacementOnRay()
            
            if new_placement is None:
                outputDialog("Could not compute placement")
                return
            
            # IMPORTANT: Restore original placement before transaction
            # This ensures undo will revert to the original state, not the preview state
            if self.original_placement is not None:
                self.component.Placement = self.original_placement
            
            # Apply with transaction (for undo support)
            FreeCAD.ActiveDocument.openTransaction("Position Component on Ray")
            try:
                self.component.Placement = new_placement
                FreeCAD.ActiveDocument.recompute()
                FreeCAD.ActiveDocument.commitTransaction()
                
                FeedbackHelper.show_success(
                    f"Component '{self.component.Label}' positioned on ray"
                )
                
                # Clear component selection (keep ray selected for next component)
                # This allows positioning multiple components on the same ray
                self.component = None
                self.original_placement = None
                self.form.componentComboBox.setCurrentIndex(0)  # Reset to "(Select Component)"
                
            except Exception as e:
                FreeCAD.ActiveDocument.abortTransaction()
                raise
                
        except Exception as e:
            FeedbackHelper.show_error_dialog(
                "Apply Failed",
                FeedbackHelper.format_error(e, "Could not apply transformation")
            )
    
    def reject(self):
        """Close/Cancel button - check for unsaved changes first."""
        import FreeCAD
        import FreeCADGui
        from PySide import QtGui
        
        # Stop any active pickers
        self.stopLinePick()
        self.stopComponentPick()
        
        # Check if component has unsaved preview changes
        has_unsaved_changes = (
            self.component is not None and 
            self.original_placement is not None and
            self.component.Placement != self.original_placement
        )
        
        if has_unsaved_changes:
            # Show confirmation dialog
            reply = QtGui.QMessageBox.question(
                None,
                "Unsaved Changes",
                f"Component '{self.component.Label}' has been moved but not applied.\n\n"
                "Do you want to apply the changes before closing?",
                QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel,
                QtGui.QMessageBox.Save  # Default button
            )
            
            if reply == QtGui.QMessageBox.Save:
                # Apply changes then close
                self.onApplyClicked()
                # onApplyClicked already clears component, so nothing to revert
                FreeCADGui.Control.closeDialog()
                return
            elif reply == QtGui.QMessageBox.Cancel:
                # Stay open, don't close
                return
            # else: Discard - continue to revert below
        
        # Restore original placement if component was modified (Discard case)
        if self.component is not None and self.original_placement is not None:
            self.component.Placement = self.original_placement
            FreeCAD.ActiveDocument.recompute()
        
        # Close panel
        FreeCADGui.Control.closeDialog()
    
    def getStandardButtons(self):
        """Return no standard buttons - we have custom buttons in UI."""
        return 0


class PositionOnRayMenu(WBCommandMenu):
    """Menu command for Position Component on Ray."""
    
    def __init__(self):
        WBCommandMenu.__init__(self, PositionOnRayGUI)
    
    def GetResources(self):
        """Return menu resources."""
        from freecad.pyoptools import ICONPATH
        import os
        
        tooltip = "Position component origin along ray line with Z-axis alignment"
        
        if not self.IsActive():
            if not FreeCAD.ActiveDocument:
                tooltip += " - Disabled: No document open"
            else:
                tooltip += " - Disabled: No optical components in document"
        
        return {
            "MenuText": "Position Component on Ray",
            "Accel": "Shift+R",  # Keyboard shortcut
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "position-on-ray.svg"),
        }
    
    def IsActive(self):
        """Enable button only when optical components exist."""
        if FreeCAD.ActiveDocument is None:
            return False
        
        # Check if any optical components exist (exclude only propagation)
        objs = FreeCAD.ActiveDocument.Objects
        optical_components = [
            obj for obj in objs
            if hasattr(obj, "ComponentType") 
            and obj.ComponentType not in ["Propagation"]
        ]
        
        return len(optical_components) > 0
