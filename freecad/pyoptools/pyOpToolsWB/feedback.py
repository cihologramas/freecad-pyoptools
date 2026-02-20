"""Visual feedback helper utilities for pyOpTools workbench.

This module provides consistent visual feedback across all pyOpTools commands,
including status messages, error dialogs, and loading indicators.

Implements requirements from Story 1.6: Add Visual Feedback System
- All feedback appears within 200ms (NFR-U4)
- Error messages are user-friendly with recovery actions (NFR-U5)
- Follows FreeCAD UI patterns and theme compatibility
"""

from PySide import QtCore, QtWidgets
import FreeCAD
import functools


class FeedbackHelper:
    """Helper class for visual feedback across pyOpTools workbench."""

    @staticmethod
    def show_success(message):
        """Show success message in FreeCAD console (green).

        Parameters
        ----------
        message : str
            Success message to display

        Example
        -------
        FeedbackHelper.show_success("Ray propagation complete - 1247 rays traced")
        """
        FreeCAD.Console.PrintMessage(f"[pyOpTools] {message}\n")

    @staticmethod
    def show_warning(message):
        """Show warning message in FreeCAD console (yellow).

        Parameters
        ----------
        message : str
            Warning message to display

        Example
        -------
        FeedbackHelper.show_warning("No components selected - using all components")
        """
        FreeCAD.Console.PrintWarning(f"[pyOpTools] {message}\n")

    @staticmethod
    def show_error(message):
        """Show error message in FreeCAD console (red).

        Parameters
        ----------
        message : str
            Error message to display

        Example
        -------
        FeedbackHelper.show_error("Ray propagation failed - no light sources found")
        """
        FreeCAD.Console.PrintError(f"[pyOpTools] {message}\n")

    @staticmethod
    def show_error_dialog(title, message, details=None):
        """Show user-friendly error dialog.

        Displays error messages in plain language with recovery actions.
        Technical details are logged to console for debugging.

        Parameters
        ----------
        title : str
            Dialog title (short description of what failed)
        message : str
            User-friendly error message with recovery action
        details : str, optional
            Technical details for debugging (logged to console, not shown to user)

        Example
        -------
        FeedbackHelper.show_error_dialog(
            "Component Insertion Failed",
            "Could not create lens component. Ensure all parameters are valid."
        )
        """
        # Log technical details to console for debugging
        if details:
            FreeCAD.Console.PrintLog(f"[pyOpTools Debug] {details}\n")

        # Show user-friendly dialog
        QtWidgets.QMessageBox.warning(None, title, message)

    @staticmethod
    def with_busy_cursor(func):
        """Decorator to show busy cursor during long operations.

        Use this decorator for operations that take >200ms.
        Cursor is always restored, even if operation fails.

        Parameters
        ----------
        func : callable
            Function to wrap with busy cursor

        Returns
        -------
        callable
            Wrapped function

        Example
        -------
        @FeedbackHelper.with_busy_cursor
        def execute(self, obj):
            # Long operation here
            perform_raytrace()
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                return func(*args, **kwargs)
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()

        return wrapper

    @staticmethod
    def format_error(exception, user_message):
        """Format exception as user-friendly message.

        Logs technical error for debugging and returns user-friendly message.
        Never shows stack traces or technical jargon to users (NFR-U5).

        Parameters
        ----------
        exception : Exception
            The exception that occurred
        user_message : str
            User-friendly explanation with recovery action

        Returns
        -------
        str
            User-friendly error message

        Example
        -------
        try:
            create_component()
        except Exception as e:
            msg = FeedbackHelper.format_error(
                e,
                "Could not create component. Please check all parameters are valid."
            )
            FeedbackHelper.show_error_dialog("Component Creation Failed", msg)
        """
        # Log technical error for debugging
        FreeCAD.Console.PrintLog(
            f"[pyOpTools Debug] {type(exception).__name__}: {str(exception)}\n"
        )

        # Return user-friendly message
        return user_message

    @staticmethod
    def with_error_handling(component_name=None, operation="creation"):
        """Decorator to add user-friendly error handling to component operations.

        Wraps a method with try-except that shows user-friendly error dialogs.
        Automatically logs technical errors for debugging.

        Behavior by operation type:
        - operation="creation": Recomputes document, updates GUI, and closes dialog
        - operation="execution": Updates GUI and closes dialog (no recompute)
        - operation="persistent": Updates GUI but keeps dialog open (for multi-run panels)
        - operation="dialog": Only provides error handling (no auto-actions)

        Parameters
        ----------
        component_name : str, optional
            Name of the component for error messages (e.g., "Spherical Lens")
            If None, uses generic "Component"
        operation : str, optional
            Type of operation:
            - "creation": Component insertion (auto-recompute + GUI update + close)
            - "execution": Other operations like optimization (GUI update + close)
            - "persistent": Task panel operations that stay open (GUI update, no close)
            - "dialog": Dialog operations (error handling only)
            Default is "creation"

        Returns
        -------
        callable
            Decorator function

        Example
        -------
        # Component creation (auto-close)
        class SphericalLensGUI(WBCommandGUI):
            @FeedbackHelper.with_error_handling("Spherical Lens")
            def accept(self):
                obj = InsertSL(...)
                obj.Placement = placement
                # No need to call recompute(), updateGui(), or closeDialog()

        # Persistent operation (stays open for multiple runs)
        class OptimizeGUI(WBCommandGUI):
            @FeedbackHelper.with_error_handling("Optimization", operation="persistent")
            def accept(self):
                result = perform_optimization(...)
                show_results(result)
                # Panel stays open for multiple optimization runs
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    # Execute the wrapped function
                    result = func(*args, **kwargs)

                    # Handle post-operation tasks based on operation type
                    if operation == "creation":
                        # Component creation: recompute, update GUI, and close dialog
                        import FreeCAD
                        import FreeCADGui

                        FreeCAD.ActiveDocument.recompute()
                        FreeCADGui.updateGui()
                        FreeCADGui.Control.closeDialog()

                    elif operation == "execution":
                        # Other operations: update GUI and close dialog (no recompute)
                        import FreeCADGui

                        FreeCADGui.updateGui()
                        FreeCADGui.Control.closeDialog()

                    elif operation == "persistent":
                        # Persistent panel operations: update GUI but keep panel open
                        import FreeCADGui

                        FreeCADGui.updateGui()
                        # Note: Dialog stays open for multiple runs

                    return result

                except Exception as e:
                    # Determine component name and operation
                    comp_name = component_name or "Component"

                    # Build error title and message based on operation type
                    if operation == "creation":
                        title = f"{comp_name} Creation Failed"
                        message = FeedbackHelper.format_error(
                            e,
                            f"Could not create {comp_name.lower()}.\n\n"
                            "Please verify:\n"
                            "• All parameters are valid (positive values where required)\n"
                            "• Material catalog and reference are correct\n"
                            "• A document is open",
                        )
                    elif operation == "dialog":
                        title = f"Failed to Open {comp_name} Dialog"
                        message = FeedbackHelper.format_error(
                            e,
                            f"Could not open the {comp_name.lower()} dialog.\n\n"
                            "Please ensure FreeCAD is properly configured and try again.",
                        )
                    else:
                        title = f"{comp_name} {operation.title()} Failed"
                        message = FeedbackHelper.format_error(
                            e,
                            f"Operation failed: {operation}\n\n"
                            "Please check the FreeCAD console for technical details.",
                        )

                    FeedbackHelper.show_error_dialog(title, message)

            return wrapper

        return decorator
