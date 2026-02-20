# Standard library imports
import os
import time
import traceback
from math import sin, cos

# Third-party imports
from numpy import array
from PySide import QtCore, QtGui

# FreeCAD imports
import FreeCAD
import FreeCADGui

# Local application imports
from freecad.pyoptools import ICONPATH
from ..wbcommand import WBCommandGUI
from ..feedback import FeedbackHelper
from ..pyoptoolshelpers import getActiveSystem, getObjectPyOptoolsPose
from ..selectionhelpers import SelectionObserver
from .merit_functions import (
    collimation_error,
    spot_size,
    x_axis_spread,
    y_axis_spread,
)
from .optimization_worker import OptimizationWorker


class EscapeKeyFilter(QtCore.QObject):
    """Event filter to handle ESC key for closing task panel."""

    def __init__(self, callback):
        """Initialize with callback to call on ESC press.

        Args:
            callback: Function to call when ESC is pressed
        """
        super(EscapeKeyFilter, self).__init__()
        self.callback = callback

    def eventFilter(self, obj, event):
        """Filter events - call callback on ESC key press."""
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Escape:
                self.callback()
                return True  # Event handled
        return False  # Pass other events through


class OptimizeGUI(WBCommandGUI):
    """GUI dialog for optical system optimization.
    
    This dialog allows users to optimize the position of optical components
    by minimizing various merit functions (collimation error, spot size, etc.).
    The optimization varies a scalar parameter (distance along a direction vector)
    to find the optimal component position.
    
    Features:
    - Multiple merit functions (collimation, spot size, x/y spread)
    - Multiple optimization solvers from scipy.optimize
    - Real-time progress tracking with parameter display
    - Accept/reject workflow for applying results
    - Keyboard shortcuts and pick-from-view functionality
    """
    def __init__(self):
        WBCommandGUI.__init__(self, "Optimize.ui")
        objs = FreeCAD.ActiveDocument.Objects
        opobjs = filter(lambda x: hasattr(x, "ComponentType"), objs)

        # Track first component and selected component for pre-selection
        first_component_index = -1
        selected_component_index = -1
        current_index = 0

        selection = FreeCADGui.Selection.getSelection()
        selected_obj = selection[0] if len(selection) > 0 else None

        for i in opobjs:
            # Exclude propagation results (not physical components to optimize)
            if i.ComponentType not in ["Propagation"]:
                self.form.Element.addItem(i.Label, i)

                # Track first component
                if first_component_index == -1:
                    first_component_index = current_index

                # Check if this is the selected object
                if selected_obj and i == selected_obj:
                    selected_component_index = current_index

                current_index += 1

            if i.ComponentType == "Sensor":
                self.form.Sensor.addItem(i.Label, i)

        # Pre-select component based on user selection or default to first
        if selected_component_index >= 0:
            # User had a component selected - use that
            self.form.Element.setCurrentIndex(selected_component_index)
        elif first_component_index >= 0:
            # No selection - use first component
            self.form.Element.setCurrentIndex(first_component_index)

        # Pre-select first sensor (existing behavior is correct)
        if self.form.Sensor.count() > 0:
            self.form.Sensor.setCurrentIndex(0)

        # Initialize pick mode state
        self.element_observer = None
        self.sensor_observer = None

        # Install event filter to handle ESC key
        self.escape_filter = EscapeKeyFilter(self.reject)
        self.form.installEventFilter(self.escape_filter)

       
        self._setupPickButton(
            self.form.PickElement,
            self.startElementPick,
            "Click to select element from 3D view",
        )
       
        self._setupPickButton(
            self.form.PickSensor,
            self.startSensorPick,
            "Click to select sensor from 3D view",
        )

        # add some possible solvers supported by scipy.minimize
        solvers = [
            "Nelder-Mead",
            "Powell",
            "CG",
            "BFGS",
            "L-BFGS-B",
            "TNC",
            "COBYLA",
            "SLSQP",
            "trust-constr",
        ]
        self.form.Solver.addItems(solvers)

        # Wire up custom buttons
       
        self.form.startButton.clicked.connect(self.accept)
       
        self.form.closeButton.clicked.connect(self.reject)
       
        self.form.stopButton.clicked.connect(self.stopOptimization)

        # Setup button icons
        self._setupButtonIcons()

        # Optimization worker thread
        self.worker = None

        # Hybrid timer setup for UI updates (10Hz = 100ms interval)
        self.ui_update_timer = QtCore.QTimer()
        self.ui_update_timer.setInterval(100)  # 100ms
        self.ui_update_timer.timeout.connect(self.checkAndUpdateUI)

        # Elapsed time timer (1Hz = 1 second interval)
        self.elapsed_timer = QtCore.QTimer()
        self.elapsed_timer.setInterval(1000)  # 1 second
        self.elapsed_timer.timeout.connect(self.updateElapsedTime)

        # Hybrid timer state
        self.dirty_flag = False
        self.last_ui_update_time = 0
        self.pending_iteration = None
        self.pending_merit = None

        # Parameter tracking state (NEW for Story 3.4)
        self.position_dirty = False
        self.pending_x = None
        self.pending_y = None
        self.pending_z = None
        self.original_x = 0.0
        self.original_y = 0.0
        self.original_z = 0.0

        # Merit function tracking (NEW for Story 3.5 enhancement)
        self.original_merit = None
        self.current_merit = None

        # Elapsed time tracking
        self.start_time = 0
        self.elapsed_seconds = 0

        # Completion data storage for Accept workflow
        self.completion_data = None

        # Connect Accept button
        
        self.form.acceptButton.clicked.connect(self.onAcceptClicked)

        accept_shortcut = QtGui.QShortcut(
            QtGui.QKeySequence("Ctrl+Return"), self.form
        )

        accept_shortcut.activated.connect(self.onAcceptShortcut)

        # Connect Element dropdown to invalidate Accept when selection changes
        self.form.Element.currentIndexChanged.connect(self.onElementChanged)

    def _setupButtonIcons(self):
        """Configure icons for action buttons using custom Tango-style icons."""

        # Get icon path from package
        try:

            FreeCAD.Console.PrintLog(f"Loading button icons from: {ICONPATH}\n")

            # Start button - green play icon
            
            icon_file = os.path.join(ICONPATH, "media-playback-start.svg")

            self.start_icon = QtGui.QIcon(icon_file)
            self.form.startButton.setIcon(self.start_icon)
            self.form.startButton.setIconSize(QtCore.QSize(16, 16))

            # Stop button - red stop octagon icon
        
            icon_file = os.path.join(ICONPATH, "process-stop.svg")
            
            self.stop_icon = QtGui.QIcon(icon_file)
            self.form.stopButton.setIcon(self.stop_icon)
            self.form.stopButton.setIconSize(QtCore.QSize(16, 16))

            # Accept button - green checkmark icon
        
            icon_file = os.path.join(ICONPATH, "dialog-ok-apply.svg")
            self.accept_icon = QtGui.QIcon(icon_file)
            self.form.acceptButton.setIcon(self.accept_icon)
            self.form.acceptButton.setIconSize(QtCore.QSize(16, 16))

            # Close button - red X icon
        
            icon_file = os.path.join(ICONPATH, "window-close.svg")
            self.close_icon = QtGui.QIcon(icon_file)
            self.form.closeButton.setIcon(self.close_icon)
            self.form.closeButton.setIconSize(QtCore.QSize(16, 16))

        except Exception as e:
            # If icon loading fails, buttons will just show without icons
            
            FreeCAD.Console.PrintError(f"Could not load button icons: {e}\n")
            FreeCAD.Console.PrintError(traceback.format_exc())

    def _setupPickButton(self, button, slot, tooltip):
        """Configure pick button with icon and tooltip.

        Args:
            button: QPushButton to configure
            slot: Function to connect to clicked signal
            tooltip: Tooltip text to display
        """

        # Connect signal
        button.clicked.connect(slot)

        # Set tooltip
        button.setToolTip(tooltip)

        # Load custom pick icon
        try: 
            icon_path = os.path.join(ICONPATH, "pick-from-view.svg")
            icon = QtGui.QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QtCore.QSize(16, 16))
        except Exception as e:
            # If icon loading fails, button will just show without icon
            FreeCAD.Console.PrintLog(f"Could not load pick button icon: {e}\n")

    def accept(self):
        """Called when user clicks Start Optimization button - launches background worker."""
        try:
            element_label = self.form.Element.currentText()
            sensor_label = self.form.Sensor.currentText()
            solver = self.form.Solver.currentText()

            system, rays = getActiveSystem()
            # Check if element is in system.complist (optical component) or is a ray source
            # Ray sources are handled differently in pyoptools
            if element_label in system.complist:
                component, position_tuple, direction = system.complist[element_label]
            else:
                # The selected object is a RaySource, which behaves differently in pyoptools
                obj = FreeCAD.ActiveDocument.getObject(element_label)
                position_tuple, direction = getObjectPyOptoolsPose(obj)
                

            # Determine optimization direction (as numpy array for vectorized operations)
            if self.form.X.isChecked():
                axis = array((1, 0, 0))  # Move along X axis
            elif self.form.Y.isChecked():
                axis = array((0, 1, 0))  # Move along Y axis
            elif self.form.Z.isChecked():
                axis = array((0, 0, 1))  # Move along Z axis
            else:
                # Arbitrary direction based on component's rotation angles (rx, ry, rz)
                # This computes the forward direction vector from Euler angles
                rx, ry, rz = direction
                axis = array((sin(rx) * sin(rz) + cos(rx) * cos(rz) * sin(ry),
                        cos(rx) * sin(ry) * sin(rz) - cos(rz) * sin(rx),
                        cos(rx) * cos(ry))) 
                
            initial_pos = array(position_tuple)
            
            # Determine merit function based on optimization type
            # Merit functions expect displacement vectors, so we wrap them to accept scalar parameters
            # and convert to displacement: displacement = param * direction_vector
            def make_merit_wrapper(func):
                """Wrap merit function to convert scalar parameter to displacement vector.
                
                The optimizer varies a scalar parameter (distance along axis).
                This wrapper converts: scalar → displacement = scalar * axis_vector
                Then calls: merit_func(displacement, element_label, sensor_label)
                """
                def wrapper(x):
                    # Extract scalar: if x is array-like use x[0], otherwise use x directly
                    param = x[0] if hasattr(x, '__getitem__') else x
                    # Calculate displacement vector and call merit function
                    displacement = param * axis
                    return func(displacement, element_label, sensor_label)
                return wrapper
            
            if self.form.Collimation.isChecked():
                merit_func = make_merit_wrapper(collimation_error)
            elif self.form.SpotSize.isChecked():
                merit_func = make_merit_wrapper(spot_size)
            elif self.form.XSize.isChecked():
                merit_func = make_merit_wrapper(x_axis_spread)
            elif self.form.YSize.isChecked():
                merit_func = make_merit_wrapper(y_axis_spread)

            self.original_x = initial_pos[0]
            self.original_y = initial_pos[1]
            self.original_z = initial_pos[2]
            
            # Store direction vector for result display
            self.optimization_direction = axis

            # NEW: Initialize parameter display
            self.initializeParameterDisplay(element_label, axis)

            # Reset merit tracking (will be populated when worker emits initial_merit_signal)
            self.original_merit = None
            self.current_merit = None

            # Show progress display
            self.form.progressGroup.setVisible(True)

            # Reset progress display
            self.resetProgressDisplay()

            # Reset Accept workflow (discard previous results if not accepted)
            self.completion_data = None
            self.form.acceptButton.setEnabled(False)
            self.form.acceptButton.setText("Accept Changes")  # Reset text
            
            # Hide warning label
            self.form.warningLabel.setVisible(False)

            # Disable Start button, enable Stop button
            self.form.startButton.setEnabled(False)
            self.form.stopButton.setEnabled(True)

            # Create and configure worker thread
            # The worker optimizes a scalar parameter (distance along direction vector)
            # which the merit_func wrapper converts to displacement vectors
            self.worker = OptimizationWorker(
                merit_func,
                0,  # Initial parameter value (distance along direction vector, typically starts at 0)
                solver,
                element_label,
                initial_pos,
                selected_axis=axis,
                max_iterations=100,
            )

            # Connect worker signals to UI slots
            self.worker.iteration_signal.connect(self.onIterationComplete)
            self.worker.position_update.connect(self.onPositionUpdate)  # NEW
            self.worker.initial_merit_signal.connect(
                self.onInitialMerit
            )  # NEW for merit display
            self.worker.status_signal.connect(self.updateStatus)
            self.worker.progress_signal.connect(self.updateProgress)
            self.worker.finished_signal.connect(self.onOptimizationComplete)
            self.worker.optimization_complete.connect(
                self.onOptimizationCompleteAccept
            )  # NEW for Accept workflow

            # Start timers
            self.start_time = time.time()
            self.elapsed_seconds = 0
            self.ui_update_timer.start()
            self.elapsed_timer.start()

            # Start worker thread
            self.worker.start()

        except Exception as e:
            # Handle any errors during optimization setup
            tb = traceback.format_exc()
            FeedbackHelper.show_error_dialog(
                "Optimization Setup Failed",
                f"Could not start optimization.\n\n"
                f"Please verify:\n"
                f"• Element and sensor are selected\n"
                f"• Optical system is properly configured\n"
                f"• All components are valid\n\n"
                f"Error: {str(e)}",
                f"Traceback:\n{tb}",
            )
            FreeCAD.Console.PrintError(tb + "*****\n")
            # Re-enable Start button if setup failed
            self.form.startButton.setEnabled(True)
            self.form.stopButton.setEnabled(False)

    def stopOptimization(self):
        """Called when user clicks Stop button - request graceful stop."""
        if self.worker and self.worker.isRunning():
            # Immediate UI feedback (<200ms requirement for NFR-U4)
            self.updateStatus("Stopping...")

            # Signal worker to stop (thread-safe)
            self.worker.stop()

            # Disable stop button to prevent double-stop
            self.form.stopButton.setEnabled(False)

    def onIterationComplete(self, iteration, merit):
        """Called via signal when iteration completes (hybrid timer strategy).

        Args:
            iteration: Current iteration number
            merit: Current merit function value
        """
        current_time = time.time() * 1000  # milliseconds

        # Store current merit for display
        self.current_merit = merit

        # Hybrid timer logic: immediate update for slow iterations, batched for fast
        if (current_time - self.last_ui_update_time) > 100:
            # Slow iteration (>100ms): Update immediately
            self.updateUINow(iteration, merit)
            self.last_ui_update_time = current_time
        else:
            # Fast iteration (<100ms): Batch via timer
            self.pending_iteration = iteration
            self.pending_merit = merit
            self.dirty_flag = True

    def onInitialMerit(self, initial_merit):
        """Called via signal when initial merit is calculated.

        Args:
            initial_merit: Initial merit function value before optimization
        """
        self.original_merit = initial_merit
        self.current_merit = initial_merit  # Start with original value

        # Update original merit label
        self.form.originalMeritLabel.setText(f"{initial_merit:.3e}")

        # Update current merit label (starts at original value)
        self.form.currentMeritLabel.setText(f"{initial_merit:.3e}")

        # No improvement yet
        self.form.meritImprovementLabel.setText("")

    def checkAndUpdateUI(self):
        """Called by QTimer every 100ms - update UI if dirty flags set."""
        if self.dirty_flag:
            self.updateUINow(self.pending_iteration, self.pending_merit)
            self.dirty_flag = False
            self.last_ui_update_time = time.time() * 1000

        # NEW: Also update parameter display if position dirty
        if self.position_dirty:
            self.updateParameterDisplayNow()

    def updateUINow(self, iteration, merit):
        """Actually update UI widgets with current values.

        Args:
            iteration: Current iteration number
            merit: Current merit function value
        """
        max_iter = self.worker.max_iterations if self.worker else 100
        self.form.iterationLabel.setText(f"Iteration: {iteration} / {max_iter}")
        self.form.meritLabel.setText(f"Merit: {merit:.6f}")

        # Update current merit in parameter tracking
        self.form.currentMeritLabel.setText(f"{merit:.3e}")

        # Calculate and display improvement percentage
        if self.original_merit is not None and self.original_merit > 0:
            improvement = (self.original_merit - merit) / self.original_merit * 100
            if improvement > 0:
                self.form.meritImprovementLabel.setText(f"(↓{improvement:.1f}%)")
                self.form.meritImprovementLabel.setStyleSheet(
                    "color: green; font-weight: bold;"
                )
            elif improvement < 0:
                self.form.meritImprovementLabel.setText(f"(↑{abs(improvement):.1f}%)")
                self.form.meritImprovementLabel.setStyleSheet(
                    "color: red; font-weight: bold;"
                )
            else:
                self.form.meritImprovementLabel.setText("")

    def updateProgress(self, percentage):
        """Update progress bar.

        Args:
            percentage: Progress percentage (0-100)
        """
        self.form.progressBar.setValue(percentage)

    def updateStatus(self, status_text):
        """Update status label with color coding.

        Args:
            status_text: Status message
        """
        # Color coding based on status
        if "Running" in status_text or "Initializing" in status_text:
            color = "#0066CC"  # Blue
        elif "Converged" in status_text:
            color = "#00AA00"  # Green
        elif "Stopped" in status_text:
            color = "#FFAA00"  # Yellow/Orange
        elif "Failed" in status_text:
            color = "#CC0000"  # Red
        else:
            color = "#000000"  # Black (default)

        self.form.statusLabel.setText(f"Status: {status_text}")
        self.form.statusLabel.setStyleSheet(f"color: {color}; font-weight: bold;")

    def updateElapsedTime(self):
        """Called every second to update elapsed time display."""
        self.elapsed_seconds = int(time.time() - self.start_time)
        minutes = self.elapsed_seconds // 60
        seconds = self.elapsed_seconds % 60
        self.form.elapsedLabel.setText(f"Elapsed: {minutes:02d}:{seconds:02d}")

    def resetProgressDisplay(self):
        """Reset all progress widgets to initial state."""
        self.form.progressBar.setValue(0)
        self.form.iterationLabel.setText("Iteration: 0 / --")
        self.form.meritLabel.setText("Merit: --")
        self.form.elapsedLabel.setText("Elapsed: --")
        self.form.statusLabel.setText("Status: Ready")
        self.form.statusLabel.setStyleSheet("")
        self.form.resultLabel.setText("")
        self.form.resultLabel.setVisible(False)

    def initializeParameterDisplay(self, component_name, selected_axis):
        """Initialize parameter tracking display at optimization start.

        Args:
            component_name: Name of component being optimized
            selected_axis: Direction array being optimized (e.g. array([1,0,0]) for X)
        """
        # Set component name
        self.form.componentNameLabel.setText(f"Component: {component_name}")

        # Display direction vector
        direction_text = f"Direction: ({selected_axis[0]:.3f}, {selected_axis[1]:.3f}, {selected_axis[2]:.3f})"
        self.form.normalVectorLabel.setText(direction_text)

        # Display original merit (if available, populated later via signal)
        if self.original_merit is not None:
            self.form.originalMeritLabel.setText(f"{self.original_merit:.3e}")
        else:
            self.form.originalMeritLabel.setText("--")

        # Display original position values
        self.form.originalXLabel.setText(f"{self.original_x:.4f} mm")
        self.form.originalYLabel.setText(f"{self.original_y:.4f} mm")
        self.form.originalZLabel.setText(f"{self.original_z:.4f} mm")

        # Initialize current merit to original value (or placeholder)
        if self.original_merit is not None:
            self.form.currentMeritLabel.setText(f"{self.original_merit:.3e}")
        else:
            self.form.currentMeritLabel.setText("--")
        self.form.meritImprovementLabel.setText("")  # No improvement yet

        # Initialize current position to original values
        self.form.currentXLabel.setText(f"{self.original_x:.4f} mm")
        self.form.currentYLabel.setText(f"{self.original_y:.4f} mm")
        self.form.currentZLabel.setText(f"{self.original_z:.4f} mm")

        # Initialize delta labels (empty at start)
        self.form.deltaXLabel.setText("")
        self.form.deltaYLabel.setText("")
        self.form.deltaZLabel.setText("")

        # Style changing vs fixed parameters
        self.styleParameterLabels(selected_axis)

    def styleParameterLabels(self, selected_axis):
        """Apply visual styling to distinguish changing vs fixed parameters.

        Args:
            selected_axis: Direction tuple/array being optimized (e.g. (1,0,0) for X, (0,1,0) for Y, etc.)
        """
        # Bold style for changing parameter
        bold_style = "font-weight: bold;"
        # Gray style for fixed parameters
        gray_style = "color: gray;"

        # Check which axes have non-zero components in direction vector
        # Use a small threshold to account for floating point precision
        threshold = 0.01
        
        has_x_component = abs(selected_axis[0]) > threshold
        has_y_component = abs(selected_axis[1]) > threshold
        has_z_component = abs(selected_axis[2]) > threshold
        
        # Apply styles: bold if axis participates in movement, gray if fixed
        self.form.currentXLabel.setStyleSheet(
            bold_style if has_x_component else gray_style
        )
        self.form.currentYLabel.setStyleSheet(
            bold_style if has_y_component else gray_style
        )
        self.form.currentZLabel.setStyleSheet(
            bold_style if has_z_component else gray_style
        )

    def onPositionUpdate(self, current_x, current_y, current_z):
        """Called via signal when worker emits position update (hybrid timer strategy).

        Args:
            current_x: Current X position value
            current_y: Current Y position value
            current_z: Current Z position value
        """
        current_time = time.time() * 1000  # milliseconds

        # Store latest values
        self.pending_x = current_x
        self.pending_y = current_y
        self.pending_z = current_z
        self.position_dirty = True

        # Hybrid timer logic: immediate update for slow iterations, batched for fast
        if (current_time - self.last_ui_update_time) > 100:
            # Slow iteration (>100ms): Update immediately
            self.updateParameterDisplayNow()
        # else: Fast iteration - let timer handle it via checkAndUpdateUI

    def updateParameterDisplayNow(self):
        """Actually update parameter display widgets with current values."""
        if not self.position_dirty:
            return

        # Update current position labels with 4 decimal places
        self.form.currentXLabel.setText(f"{self.pending_x:.4f} mm")
        self.form.currentYLabel.setText(f"{self.pending_y:.4f} mm")
        self.form.currentZLabel.setText(f"{self.pending_z:.4f} mm")

        # Calculate and display deltas with +/- sign
        delta_x = self.pending_x - self.original_x
        delta_y = self.pending_y - self.original_y
        delta_z = self.pending_z - self.original_z

        if abs(delta_x) > 0.0001:  # Only show non-zero deltas
            self.form.deltaXLabel.setText(f"({delta_x:+.4f})")
        else:
            self.form.deltaXLabel.setText("(fixed)")

        if abs(delta_y) > 0.0001:
            self.form.deltaYLabel.setText(f"({delta_y:+.4f})")
        else:
            self.form.deltaYLabel.setText("(fixed)")

        if abs(delta_z) > 0.0001:
            self.form.deltaZLabel.setText(f"({delta_z:+.4f})")
        else:
            self.form.deltaZLabel.setText("(fixed)")

        self.position_dirty = False

    def onOptimizationComplete(self, success, result):
        """Called when optimization completes or fails.

        Args:
            success: True if optimization converged successfully
            result: scipy OptimizeResult object (or None if error)
        """
        # Stop timers
        self.ui_update_timer.stop()
        self.elapsed_timer.stop()

        # Re-enable Start button, disable Stop button
        self.form.startButton.setEnabled(True)
        self.form.stopButton.setEnabled(False)

        # Wait for worker thread to finish
        if self.worker:
            self.worker.wait()

        # Display result if successful
        if success and result:
            # Extract scalar value from result.x (always ndarray per scipy docs)
            optimum_distance = result.x[0]
            
            # Show distance moved along direction vector
            direction_str = f"({self.optimization_direction[0]:.3f}, {self.optimization_direction[1]:.3f}, {self.optimization_direction[2]:.3f})"
            result_text = f"✓ Optimum distance = {optimum_distance:.6f} mm along {direction_str}"

            # Show result in progress window
            self.form.resultLabel.setText(result_text)
            self.form.resultLabel.setVisible(True)

        elif not success and result:
            # Stopped by user or failed - show best result found so far
            # Extract scalar value from result.x (always ndarray per scipy docs)
            best_distance = result.x[0]
            
            # Show best distance found along direction vector
            direction_str = f"({self.optimization_direction[0]:.3f}, {self.optimization_direction[1]:.3f}, {self.optimization_direction[2]:.3f})"
            result_text = f"⚠ Best distance = {best_distance:.6f} mm along {direction_str} (stopped/failed)"

            # Show intermediate result in progress window
            self.form.resultLabel.setText(result_text)
            self.form.resultLabel.setVisible(True)
        elif result is None:
            # Error occurred before any result
            self.form.resultLabel.setText("✗ Optimization failed")
            self.form.resultLabel.setVisible(True)
            # Error details already printed to console by worker thread

    def onOptimizationCompleteAccept(self, completion_data):
        """Handle optimization completion for Accept workflow.

        Args:
            completion_data: Dict with status, merit, position, warnings
        """
        # Store completion data for Accept button
        self.completion_data = completion_data

        # Enable Accept button
        self.form.acceptButton.setEnabled(True)

        # Display warnings if any
        if completion_data.get("warnings"):
            warning_text = "\n".join(completion_data["warnings"])
            self.form.warningLabel.setText(warning_text)
            self.form.warningLabel.setVisible(True)
        else:
            # Hide warning label if no warnings
            self.form.warningLabel.setVisible(False)

    def onAcceptClicked(self):
        """Handle Accept button click - apply optimized values to FreeCAD component atomically."""
        if not self.completion_data:
            FreeCAD.Console.PrintWarning("No optimization results to accept\n")
            return

        try:
            # Get final values from completion data
            final_x = self.completion_data["final_x"]
            final_y = self.completion_data["final_y"]
            final_z = self.completion_data["final_z"]

            # Get component object
            component = self.form.Element.itemData(self.form.Element.currentIndex())
            if not component:
                FreeCAD.Console.PrintError("Cannot find component to update\n")
                return

            # Start transaction for undo history
            FreeCAD.ActiveDocument.openTransaction("Apply Optimization")

            try:
                # Update position atomically
                new_position = FreeCAD.Vector(final_x, final_y, final_z)
                component.Placement.Base = new_position

                # Trigger recompute (3D view update)
                FreeCAD.ActiveDocument.recompute()

                # Commit transaction
                FreeCAD.ActiveDocument.commitTransaction()

                # Success feedback
                FreeCAD.Console.PrintMessage(
                    f"Optimization accepted for {component.Label}\n"
                )

                # Update button state
                self.form.acceptButton.setText("Accepted ✓")
                self.form.acceptButton.setEnabled(False)

                # Clear completion data
                self.completion_data = None

            except Exception as e:
                # Rollback on failure
                FreeCAD.ActiveDocument.abortTransaction()
                FreeCAD.Console.PrintError(f"Failed to apply optimization: {str(e)}\n")
                # Keep Accept button enabled for retry

        except Exception as e:
            FreeCAD.Console.PrintError(f"Accept button error: {str(e)}\n")

    def onAcceptShortcut(self):
        """Handle Ctrl+Enter keyboard shortcut - trigger Accept if button enabled."""
        if self.form.acceptButton.isEnabled():
            self.onAcceptClicked()

    def onElementChanged(self, index):
        """Handle Element dropdown selection change - discard optimization results.
        
        Args:
            index: New index in Element dropdown
        """
        # Discard any optimization results when user switches component
        self.completion_data = None
        self.form.acceptButton.setEnabled(False)
        self.form.warningLabel.setVisible(False)

    def startElementPick(self):
        """Start pick mode for Element dropdown."""
        # If already picking, toggle off
        if self.element_observer is not None:
            self.stopElementPick()
            return

        # Stop sensor pick if active
        if self.sensor_observer is not None:
            self.stopSensorPick()

        # Create and register observer
        self.element_observer = SelectionObserver(
            callback=self.onElementPicked,
            filter_func=self.isOpticalComponent,
            error_message="Please select an optical component (not a ray source or sensor)",
        )
        FreeCADGui.Selection.addObserver(self.element_observer)

        # Visual feedback
        self.form.PickElement.setDown(True)
        FreeCAD.Console.PrintMessage("Click on optical component in 3D view\n")

        # Change cursor to crosshair globally
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)

    def stopElementPick(self):
        """Stop pick mode for Element dropdown."""
        if self.element_observer is not None:
            FreeCADGui.Selection.removeObserver(self.element_observer)
            self.element_observer = None

        # Reset button state
        self.form.PickElement.setDown(False)
        self.form.PickElement.setChecked(False)

        # Restore normal cursor
        QtGui.QApplication.restoreOverrideCursor()

    def onElementPicked(self, obj, sub):
        """Called when valid optical component picked.

        Args:
            obj: FreeCAD object that was selected
            sub: Sub-element (ignored for component selection)
        """
        # Find object in dropdown and select it
        for i in range(self.form.Element.count()):
            if self.form.Element.itemData(i) == obj:
                self.form.Element.setCurrentIndex(i)
                break

        # Cleanup
        self.stopElementPick()

    def isOpticalComponent(self, obj, sub):
        """Validate object is optical component (not ray or sensor).

        Args:
            obj: FreeCAD object to check
            sub: Sub-element (ignored for component selection)

        Returns:
            bool: True if object is valid optical component
        """
        if obj is None:
            return False

        if not hasattr(obj, "ComponentType"):
            return False

        # Exclude propagation results (same filter as dropdown)
        return obj.ComponentType not in ["Propagation"]

    def startSensorPick(self):
        """Start pick mode for Sensor dropdown."""
        # If already picking, toggle off
        if self.sensor_observer is not None:
            self.stopSensorPick()
            return

        # Stop element pick if active
        if self.element_observer is not None:
            self.stopElementPick()

        # Create and register observer
        self.sensor_observer = SelectionObserver(
            callback=self.onSensorPicked,
            filter_func=self.isSensor,
            error_message="Please select a sensor",
        )
        FreeCADGui.Selection.addObserver(self.sensor_observer)

        # Visual feedback
        self.form.PickSensor.setDown(True)
        FreeCAD.Console.PrintMessage("Click on sensor in 3D view\n")

        # Change cursor to crosshair globally
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)

    def stopSensorPick(self):
        """Stop pick mode for Sensor dropdown."""
        if self.sensor_observer is not None:
            FreeCADGui.Selection.removeObserver(self.sensor_observer)
            self.sensor_observer = None

        # Reset button state
        self.form.PickSensor.setDown(False)
        self.form.PickSensor.setChecked(False)

        # Restore normal cursor
        QtGui.QApplication.restoreOverrideCursor()

    def onSensorPicked(self, obj, sub):
        """Called when valid sensor picked.

        Args:
            obj: FreeCAD object that was selected
            sub: Sub-element (ignored for component selection)
        """
        # Find object in dropdown and select it
        for i in range(self.form.Sensor.count()):
            if self.form.Sensor.itemData(i) == obj:
                self.form.Sensor.setCurrentIndex(i)
                break

        # Cleanup
        self.stopSensorPick()

    def isSensor(self, obj, sub):
        """Validate object is a sensor.

        Args:
            obj: FreeCAD object to check
            sub: Sub-element (ignored for component selection)

        Returns:
            bool: True if object is sensor
        """
        if obj is None:
            return False

        if not hasattr(obj, "ComponentType"):
            return False

        # Same filter as dropdown population
        return obj.ComponentType == "Sensor"

    def hideEvent(self, event):
        """Called when dialog hidden/closed - cleanup observers and worker thread."""
        self.stopElementPick()
        self.stopSensorPick()

        # Stop optimization if running
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()  # Wait for thread to finish

        # Stop timers
        self.ui_update_timer.stop()
        self.elapsed_timer.stop()

        # Call parent class handler if it exists
        if hasattr(super(), "hideEvent"):
            super().hideEvent(event)

    def reject(self):
        """Handle Close button or ESC key - cleanup and close panel."""
        # Check if there are unapplied optimization results
        if self.completion_data is not None:
            # Show warning dialog
            reply = QtGui.QMessageBox.warning(
                None,
                "Unapplied Changes",
                "You have optimization results that haven't been applied.\n\n"
                "Do you want to close without applying the changes?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                QtGui.QMessageBox.No  # Default to No
            )
            
            # If user clicks No, cancel the close operation
            if reply == QtGui.QMessageBox.No:
                return
        
        self.stopElementPick()
        self.stopSensorPick()

        # Stop optimization if running
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()  # Wait for thread to finish

        # Stop timers
        self.ui_update_timer.stop()
        self.elapsed_timer.stop()

        FreeCADGui.Control.closeDialog()

    def getStandardButtons(self):
        """Return no standard buttons - we have custom buttons in the UI."""
        return 0  # No standard buttons

