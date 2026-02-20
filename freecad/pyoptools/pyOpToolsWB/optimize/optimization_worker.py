"""Background worker thread for optical optimization.

This module provides OptimizationWorker, a QThread-based worker that runs
scipy optimization in the background with real-time progress updates via Qt signals.

The worker optimizes a component's position by moving it along an arbitrary direction
vector. The optimization parameter is a scalar distance along this direction.

The worker handles:
    - Thread-safe stop requests
    - Real-time iteration progress updates
    - Parameter position tracking (X, Y, Z) as component moves
    - Merit function improvement tracking
    - Completion data preparation for Accept workflow
"""

# Standard library imports
import threading
import traceback

# Third-party imports
from numpy import array
from PySide import QtCore
from scipy.optimize import minimize

# FreeCAD imports
import FreeCAD


# Minimum improvement percentage to consider optimization successful
MIN_IMPROVEMENT_THRESHOLD = 5.0  # percent

class OptimizationWorker(QtCore.QThread):
    """Background worker thread for running optimization with real-time progress updates.

    Uses Qt signals for thread-safe communication with UI thread.
    Implements scipy callback for iteration tracking and graceful stop.
    """

    # Qt signals for progress updates (thread-safe, automatically queued)
    iteration_signal = QtCore.Signal(int, float)  # (iteration_num, merit_value)
    position_update = QtCore.Signal(
        float, float, float
    )  # (current_x, current_y, current_z)
    status_signal = QtCore.Signal(str)  # Status text
    progress_signal = QtCore.Signal(int)  # Percentage (0-100)
    finished_signal = QtCore.Signal(bool, object)  # (success, result)
    optimization_complete = QtCore.Signal(dict)  # Completion data for Accept workflow
    initial_merit_signal = QtCore.Signal(float)  # Initial merit value for display

    def __init__(
        self,
        merit_func,
        initial_value,
        solver,
        component_label,
        original_position,
        selected_axis,
        max_iterations,
    ):
        """Initialize optimization worker.

        Args:
            merit_func: Merit function to optimize (callable)
            initial_value: Initial parameter value (distance along direction, usually 0)
            solver: Scipy solver method name
            component_label: Label of FreeCAD component being optimized
            original_position: Tuple of (x, y, z) initial position in mm
            selected_axis: Direction vector tuple/array (e.g. (1,0,0) for X, (0,1,0) for Y, 
                          or arbitrary direction from component rotation)
            max_iterations: Maximum iterations (default 100)
        """
        super(OptimizationWorker, self).__init__()
        self.merit_func = merit_func
        self.initial_value = initial_value
        self.solver = solver
        self.max_iterations = max_iterations
        self.selected_axis = array(selected_axis)
        
        self.original_x = original_position[0]
        self.original_y = original_position[1]
        self.original_z = original_position[2]

        # Thread-safe stop flag using threading.Lock
        self._stop_flag = False
        self._stop_lock = threading.Lock()

        # Iteration tracking
        self.iteration_counter = 0

        # Merit function tracking for completion data
        self.initial_merit = None
        self.final_merit = None

        # Store component reference for Accept workflow
        self.component_label = component_label

        self.last_result = None  # Store last result for access in callback and completion

    def stop(self):
        """Request optimization to stop gracefully (thread-safe)."""
        with self._stop_lock:
            self._stop_flag = True

    def _is_stopped(self):
        """Check if stop has been requested (thread-safe)."""
        with self._stop_lock:
            return self._stop_flag

    def _map_param_to_position(self, param_value):
        """Map optimization parameter to (x, y, z) position based on direction vector.
        
        The optimization parameter is a scalar distance along the direction vector.
        This function computes: position = original_position + param_value * direction
        
        Args:
            param_value: Current parameter value from optimizer (distance along direction)
            
        Returns:
            Tuple of (x, y, z) position values in mm
        """
        return array((self.original_x, self.original_y, self.original_z))+param_value*self.selected_axis

    def _prepare_completion_data(self, result, stopped=False):
        """Prepare completion data dictionary for Accept workflow.

        Args:
            result: scipy OptimizeResult object
            stopped: True if stopped by user

        Returns:
            dict: Completion data with status, merit, position, warnings
        """
        # Extract final parameter value (result.x is always ndarray per scipy docs)
        final_param = result.x[0]

        # Map parameter to X, Y, Z based on selected axis
        final_x, final_y, final_z = self._map_param_to_position(final_param)

        # Determine status
        if stopped:
            status = "Stopped by user"
        elif result.success:
            status = "Converged"
        else:
            status = "Failed"

        # Prepare completion data
        completion_data = {
            "status": status,
            "iterations": result.nit
            if hasattr(result, "nit")
            else self.iteration_counter,
            "final_merit": result.fun,
            "initial_merit": self.initial_merit if self.initial_merit else 0.0,
            "final_x": final_x,
            "final_y": final_y,
            "final_z": final_z,
            "original_x": self.original_x,
            "original_y": self.original_y,
            "original_z": self.original_z,
            "component_name": self.component_label,
            "warnings": [],
        }

        # Detect warnings
        if self.initial_merit and self.initial_merit > 0:
            improvement = (self.initial_merit - result.fun) / self.initial_merit * 100
            if improvement < MIN_IMPROVEMENT_THRESHOLD:
                completion_data["warnings"].append(
                    f"⚠️ Merit function improved by only {improvement:.1f}%. Results may not be optimal."
                )

        if not result.success and not stopped:
            completion_data["warnings"].append(
                "⚠️ Algorithm did not fully converge. Consider increasing iteration limit."
            )

        if stopped:
            completion_data["warnings"].append(
                "⚠️ Optimization stopped early by user. Results are partial."
            )

        return completion_data

    def run(self):
        """Run optimization in background thread (called by QThread.start())."""
        try:
            self.status_signal.emit("Initializing...")
            self.iteration_counter = 0

            # Calculate initial merit for improvement tracking
            self.initial_merit = self.merit_func(0)

            # Emit initial merit to UI for display
            self.initial_merit_signal.emit(self.initial_merit)

            # Scipy callback function (runs in this worker thread)
            # CRITICAL: Parameter MUST be named 'intermediate_result' for scipy to pass OptimizeResult
            def callback(intermediate_result):
                """Called by scipy after each iteration.

                Args:
                    intermediate_result: OptimizeResult object with current state
                        - intermediate_result.fun: current merit function value
                        - intermediate_result.x: current parameter vector

                Raises:
                    StopIteration: To signal scipy to stop optimization gracefully
                """
                # Check stop flag (thread-safe read)
                if self._is_stopped():
                    raise StopIteration  # Signal scipy to stop gracefully

                # Get current merit value from scipy (no need to re-evaluate!)
                current_merit = intermediate_result.fun

                # Emit progress signals (queued to main thread automatically)
                self.iteration_signal.emit(self.iteration_counter, current_merit)

                self.last_result = intermediate_result  # Store last result for access in completion
                
                # Extract current parameter value and emit position update
                # scipy parameter is always ndarray, extract first element
                current_param = intermediate_result.x[0]

                # Map parameter to X, Y, Z based on selected axis
                current_x, current_y, current_z = self._map_param_to_position(current_param)

                # Emit position update signal (primitives only, thread-safe)
                self.position_update.emit(current_x, current_y, current_z)

                # Calculate progress percentage
                if self.max_iterations > 0:
                    progress_pct = int(
                        (self.iteration_counter / self.max_iterations) * 100
                    )
                    progress_pct = min(progress_pct, 100)  # Cap at 100%
                    self.progress_signal.emit(progress_pct)

                self.iteration_counter += 1

            # Emit running status
            self.status_signal.emit("Running...")

            # Run scipy optimization with callback
            result = minimize(
                self.merit_func,
                0,
                method=self.solver,
                callback=callback,
                options={"maxiter": self.max_iterations},
            )

            # Set progress to 100% when complete (even if converged early)
            self.progress_signal.emit(100)

            # Store final merit
            self.final_merit = result.fun

            # Prepare completion data for Accept workflow
            completion_data = self._prepare_completion_data(
                result, stopped=self._is_stopped()
            )

            # Emit completion signal BEFORE status signals for proper sequencing
            self.optimization_complete.emit(completion_data)

            # Check if stopped by user
            if self._is_stopped():
                self.status_signal.emit("Stopped by user")
                self.finished_signal.emit(False, result)
            elif result.success:
                self.status_signal.emit("Converged")
                self.finished_signal.emit(True, result)
            else:
                self.status_signal.emit("Failed")
                self.finished_signal.emit(False, result)

        except StopIteration:
            # User requested stop via callback - prepare partial results
            self.status_signal.emit("Stopped by user")

            # Emit completion data with partial results (if available)
            if self.last_result is not None:
                completion_data = self._prepare_completion_data(
                    result=self.last_result, stopped=True)
                self.optimization_complete.emit(completion_data)
            
            self.finished_signal.emit(False, self.last_result)
        except Exception as e:
            # Handle any errors during optimization
            FreeCAD.Console.PrintError(f"Optimization error: {e}\n")
            FreeCAD.Console.PrintError(f"Full traceback:\n{traceback.format_exc()}\n")
            self.status_signal.emit("Failed")
            self.finished_signal.emit(False, None)

