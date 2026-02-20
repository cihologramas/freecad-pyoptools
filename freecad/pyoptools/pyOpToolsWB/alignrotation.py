# -*- coding: utf-8 -*-
"""Align component axis to global plane (rotation around Z-axis only)."""

import FreeCAD
import FreeCADGui
from math import degrees, radians, atan2, pi
from PySide import QtCore, QtGui, QtWidgets

from .wbcommand import WBCommandGUI, WBCommandMenu
from .feedback import FeedbackHelper
from .qthelpers import outputDialog
from .selectionhelpers import SelectionObserver


class AlignRotationGUI(WBCommandGUI):
    """GUI for aligning component rotation to global planes."""
    
    def __init__(self):
        """Initialize UI and state."""
        WBCommandGUI.__init__(self, "AlignRotation.ui")
        
        # State tracking
        self.component = None           # Selected component
        self.original_placement = None  # For Cancel/restore
        self.component_observer = None  # SelectionObserver
        
        # Populate component dropdown
        self._populateComponentDropdown()
        
        # Connect signals for real-time preview
        self.form.componentComboBox.currentIndexChanged.connect(self.onComponentDropdownChanged)
        self.form.alignAxisX.toggled.connect(self.updatePreview)
        self.form.alignAxisY.toggled.connect(self.updatePreview)
        self.form.planeXY.toggled.connect(self.updatePreview)
        self.form.planeYZ.toggled.connect(self.updatePreview)
        self.form.planeZX.toggled.connect(self.updatePreview)
        self.form.reverseCheckBox.stateChanged.connect(self.updatePreview)
        
        # Setup pick button with icon
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
    
    # === Component Picking Methods ===
    
    def startComponentPick(self):
        """Start pick mode for component selection."""
        import FreeCAD
        import FreeCADGui
        
        # If already picking, toggle off
        if self.component_observer is not None:
            self.stopComponentPick()
            return
        
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
        """Called when component dropdown changes."""
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
    
    def computeAlignedRotation(self):
        """Compute rotation to align component axis perpendicular to plane normal.
        
        Uses scipy.optimize to find the rotation angle θ around component's Z-axis 
        such that: rotated_axis · plane_normal = 0
        
        Always computes from the ORIGINAL placement, not current preview state.
        
        Returns:
            FreeCAD.Placement: New placement, or None if inputs invalid
        """
        if self.component is None:
            return None
        
        import FreeCAD
        from scipy.optimize import minimize_scalar
        
        # IMPORTANT: Use original placement, not current (which may be a preview)
        if self.original_placement is None:
            # If no original stored, use current (first time)
            original_placement = self.component.Placement
        else:
            original_placement = self.original_placement
        
        current_position = original_placement.Base
        current_rotation = original_placement.Rotation
        
        # Get user inputs
        align_axis = "X" if self.form.alignAxisX.isChecked() else "Y"
        
        if self.form.planeXY.isChecked():
            global_plane = "XY"
        elif self.form.planeYZ.isChecked():
            global_plane = "YZ"
        else:
            global_plane = "ZX"
        
        reverse = self.form.reverseCheckBox.isChecked()
        
        # Define plane normals (perpendicular to the plane)
        plane_normals = {
            "XY": FreeCAD.Vector(0, 0, 1),  # Z-axis perpendicular to XY plane
            "YZ": FreeCAD.Vector(1, 0, 0),  # X-axis perpendicular to YZ plane
            "ZX": FreeCAD.Vector(0, 1, 0),  # Y-axis perpendicular to ZX plane
        }
        N = plane_normals[global_plane]  # Normal vector
        
        # Get current component axes from rotation matrix
        rotation_matrix = current_rotation.toMatrix()
        current_x = FreeCAD.Vector(rotation_matrix.A11, rotation_matrix.A21, rotation_matrix.A31)
        current_y = FreeCAD.Vector(rotation_matrix.A12, rotation_matrix.A22, rotation_matrix.A32)
        current_z = FreeCAD.Vector(rotation_matrix.A13, rotation_matrix.A23, rotation_matrix.A33)
        
        # Select which axis to align
        initial_axis = current_x if align_axis == "X" else current_y
        Z = current_z  # Rotation axis
        
        # Objective function: minimize |rotated_axis · N|²
        def objective(theta_deg):
            # Rotate initial_axis around Z by angle theta (in degrees)
            rot = FreeCAD.Rotation(Z, theta_deg)
            test_rotation = rot.multiply(current_rotation)
            
            # Get the rotated axis
            test_matrix = test_rotation.toMatrix()
            if align_axis == "X":
                rotated_axis = FreeCAD.Vector(test_matrix.A11, test_matrix.A21, test_matrix.A31)
            else:
                rotated_axis = FreeCAD.Vector(test_matrix.A12, test_matrix.A22, test_matrix.A32)
            
            # Return squared dot product (we want this to be 0)
            dot_product = rotated_axis.dot(N)
            return dot_product * dot_product
        
        # Optimize over angle range [0, 180] degrees
        # (the other solution is always 180° away, handled by "Reverse" checkbox)
        result = minimize_scalar(objective, bounds=(0, 180), method='bounded')
        
        if not result.success or result.fun > 1e-6:
            FreeCAD.Console.PrintWarning(
                f"Optimization failed or no good solution found.\n"
                f"Residual: {result.fun:.6f}\n"
            )
            # Continue anyway with best result
        
        angle_deg = result.x
        
        # Apply reverse if requested (rotate to opposite solution)
        if reverse:
            angle_deg = angle_deg + 180
        
        # No normalization needed: angle is always in [0, 360]
        
        # Debug output
        FreeCAD.Console.PrintMessage(f"=== Align Rotation Debug ===\n")
        FreeCAD.Console.PrintMessage(f"Goal: Make {align_axis}-axis perpendicular to {global_plane} plane normal\n")
        FreeCAD.Console.PrintMessage(f"Plane normal N: {N}\n")
        FreeCAD.Console.PrintMessage(f"Current {align_axis}-axis: {initial_axis}\n")
        FreeCAD.Console.PrintMessage(f"  Dot with plane normal: {initial_axis.dot(N):.6f}\n")
        FreeCAD.Console.PrintMessage(f"Rotation axis Z: {Z}\n")
        FreeCAD.Console.PrintMessage(f"Optimization result: {result.fun:.9f}\n")
        FreeCAD.Console.PrintMessage(f"Rotation angle: {angle_deg:.2f}°\n")
        FreeCAD.Console.PrintMessage(f"============================\n")
        
        # Apply rotation around current Z-axis (angle in degrees)
        z_rotation = FreeCAD.Rotation(Z, angle_deg)
        new_rotation = z_rotation.multiply(current_rotation)
        
        # Verify result
        new_matrix = new_rotation.toMatrix()
        new_x = FreeCAD.Vector(new_matrix.A11, new_matrix.A21, new_matrix.A31)
        new_y = FreeCAD.Vector(new_matrix.A12, new_matrix.A22, new_matrix.A32)
        new_z = FreeCAD.Vector(new_matrix.A13, new_matrix.A23, new_matrix.A33)
        new_axis = new_x if align_axis == "X" else new_y
        
        dot_result = new_axis.dot(N)
        
        FreeCAD.Console.PrintMessage(f"After rotation:\n")
        FreeCAD.Console.PrintMessage(f"  New {align_axis}-axis: {new_axis}\n")
        FreeCAD.Console.PrintMessage(f"  New Z-axis: {new_z}\n")
        FreeCAD.Console.PrintMessage(f"  Dot with plane normal: {dot_result:.6f} (target: 0.0)\n")
        FreeCAD.Console.PrintMessage(f"  Success: {abs(dot_result) < 0.001}\n\n")
        
        # Return new placement (same position, updated rotation)
        return FreeCAD.Placement(current_position, new_rotation)
    
    # === Preview and Apply ===
    
    def updatePreview(self):
        """Update component rotation in real-time (preview)."""
        if self.component is None:
            return
        
        try:
            # Compute new placement
            new_placement = self.computeAlignedRotation()
            
            if new_placement is not None:
                # Update component (real-time preview)
                self.component.Placement = new_placement
                FreeCAD.ActiveDocument.recompute()
        except Exception as e:
            # Silently ignore errors during preview
            FreeCAD.Console.PrintWarning(f"Preview update failed: {e}\n")
    
    def onApplyClicked(self):
        """Apply button - commit transformation with transaction."""
        if self.component is None:
            outputDialog("Please select a component")
            return
        
        try:
            # Compute new placement
            new_placement = self.computeAlignedRotation()
            
            if new_placement is None:
                outputDialog("Could not compute alignment (check plane selection)")
                return
            
            # IMPORTANT: Restore original placement before transaction
            # This ensures undo will revert to the original state, not the preview state
            if self.original_placement is not None:
                self.component.Placement = self.original_placement
            
            # Apply with transaction (for undo support)
            FreeCAD.ActiveDocument.openTransaction("Align Component Rotation")
            try:
                self.component.Placement = new_placement
                FreeCAD.ActiveDocument.recompute()
                FreeCAD.ActiveDocument.commitTransaction()
                
                FeedbackHelper.show_success(
                    f"Component '{self.component.Label}' rotation aligned"
                )
                
                # Clear component selection after successful apply
                # Allows quickly aligning multiple components with same settings
                self.component = None
                self.original_placement = None
                self.form.componentComboBox.setCurrentIndex(0)  # Reset to "(Select Component)"
                
            except Exception as e:
                FreeCAD.ActiveDocument.abortTransaction()
                raise
                
        except Exception as e:
            FeedbackHelper.show_error_dialog(
                "Apply Failed",
                FeedbackHelper.format_error(e, "Could not apply alignment")
            )
    
    def reject(self):
        """Close/Cancel button - check for unsaved changes first."""
        import FreeCAD
        import FreeCADGui
        from PySide import QtGui
        
        # Stop any active pickers
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
                f"Component '{self.component.Label}' has been rotated but not applied.\n\n"
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


class AlignRotationMenu(WBCommandMenu):
    """Menu command for Align Component Rotation."""
    
    def __init__(self):
        WBCommandMenu.__init__(self, AlignRotationGUI)
    
    def GetResources(self):
        """Return menu resources."""
        from freecad.pyoptools import ICONPATH
        import os
        
        tooltip = "Align component axis to global plane (rotation around Z-axis)"
        
        if not self.IsActive():
            if not FreeCAD.ActiveDocument:
                tooltip += " - Disabled: No document open"
            else:
                tooltip += " - Disabled: No optical components in document"
        
        return {
            "MenuText": "Align Component Rotation",
            "Accel": "Shift+A",  # Keyboard shortcut
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "align-rotation.svg"),
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
