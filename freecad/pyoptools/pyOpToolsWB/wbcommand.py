# -*- coding: utf-8 -*-

"""Helper classes used in the workbench creation."""

import FreeCAD
import FreeCADGui
from freecad.pyoptools.pyOpToolsWB.qthelpers import getUIFilePath
from PySide import QtGui, QtWidgets

from .wbpart import WBPart
from .feedback import FeedbackHelper


class widgetMix(QtWidgets.QDialog):
    """Class to emulate a QDialog where multiple widgets behave as one.

    This class has an addWidget method, that allows to "merge" the widgets so
    they behave as if all the widget definitions belong to one single widget.
    If the widget is passed with a "name", the attributes of such widget will
    appear inside an attribute of the widgetMix. This allows to include in the
    same widget, several copies of one widget, and be able to access the
    attributes of such widgets independently.
    """

    def __init__(self, parent=None):
        super(widgetMix, self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.widgets = []
        self.extra_attribs = {}

    def addWidget(self, w, name=None):
        """Add a widget to the widget mix.

        Parameters
        ----------

        w : QWidget
            Widget to add to the widgetMix
        name : str or None
            If not given (or none), the attributes of w will be accessible
            directly from the widgetMix. Care must be taken as if multiple
            widgets with the same attributes are added, only the attribute from
            the first widget added will be accessible shadowing the others. This
            can be solved by giving the widget a "name", so it will be
            accessible as "widgetMix.name".

        TODO:
        -----
        No revision is made to avoid attributes shadowing. This must
        be fixed in the future.
        """

        self.layout.addWidget(w)
        if name is None:
            self.widgets.append(w)
        elif isinstance(name, str):
            self.extra_attribs[name] = w

    def __getattr__(self, name):
        """Get the attributes from the registered widgets."""
        # Check first in the widgets regostared with no name
        for w in self.widgets:
            try:
                return getattr(w, name)
            except AttributeError:
                pass
        try:
            return self.extra_attribs[name]
        except KeyError:
            raise AttributeError

    def reject(self):
        """Handle dialog cancellation (ESC key or Cancel button).

        When used with FreeCAD's Control.showDialog(), we must explicitly
        call closeDialog() to properly clean up the FreeCAD control panel.

        This fixes the issue where pressing ESC would close the widget view
        but leave the OK/Cancel buttons visible.
        """
        FreeCADGui.Control.closeDialog()


class WBCommandGUI:
    def __init__(self, gui):
        if isinstance(gui, str):
            fn = getUIFilePath(gui)
            self.form = FreeCADGui.PySideUic.loadUi(fn)
        elif isinstance(gui, list):
            self.form = widgetMix()
            for w in gui:
                if isinstance(w, str):
                    fn = getUIFilePath(w)
                    nw = FreeCADGui.PySideUic.loadUi(fn)
                    self.form.addWidget(nw)
                elif isinstance(w, QtWidgets.QWidget):
                    self.form.addWidget(w)
                elif isinstance(w, dict):
                    for name, nw in w.items():
                        self.form.addWidget(nw, name)
                else:
                    raise ValueError
        else:
            raise ValueError


class WBCommandMenu:
    def __init__(self, gui):
        self.gui = gui

    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
            return False
        else:
            return True

    def _get_tooltip_with_disabled_reason(
        self, base_tooltip, disabled_reason="No document open"
    ):
        """Helper method to generate tooltip with disabled reason if applicable.

        Args:
            base_tooltip: The base tooltip text
            disabled_reason: The reason why the command is disabled (default: "No document open")

        Returns:
            str: Tooltip with disabled reason appended if command is not active

        Example:
            def GetResources(self):
                tooltip = self._get_tooltip_with_disabled_reason(
                    "Insert spherical lens (Ctrl+L)",
                    "No document open"
                )
                return {"ToolTip": tooltip, ...}
        """
        if not self.IsActive():
            return f"{base_tooltip} - Disabled: {disabled_reason}"
        return base_tooltip

    def Activated(self):
        """Show the component dialog with automatic error handling.

        This method wraps the dialog display with user-friendly error handling.
        Subclasses can override this method if needed, but should call super().Activated()
        or use the @FeedbackHelper.with_error_handling decorator.
        """
        try:
            sl = self.gui()
            FreeCADGui.Control.showDialog(sl)
        except Exception as e:
            # Get component name from GetResources if available
            component_name = "Component"
            try:
                if hasattr(self, "GetResources"):
                    resources = self.GetResources()
                    component_name = resources.get("MenuText", "Component")
            except:
                pass

            FeedbackHelper.show_error_dialog(
                f"Failed to Open {component_name} Dialog",
                FeedbackHelper.format_error(
                    e,
                    f"Could not open the {component_name.lower()} creation dialog.\n\n"
                    "Please ensure FreeCAD is properly configured and try again.",
                ),
            )
