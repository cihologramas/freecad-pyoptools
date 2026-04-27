import FreeCAD

_wrn = FreeCAD.Console.PrintWarning

# Module-level accumulator for forward-version warnings.
# Each entry is a string with per-object warning details.
# A single consolidated popup is shown after all objects are restored.
_forward_warn_accumulator = []
_forward_warn_timer = None


def _show_forward_version_popup():
    """Show a single consolidated popup for all forward-version warnings."""
    global _forward_warn_accumulator, _forward_warn_timer

    _forward_warn_timer = None

    if not _forward_warn_accumulator:
        return

    entries = "\n".join(_forward_warn_accumulator)
    msg = (
        "WARNING: This document contains objects saved with a newer\n"
        "version of the pyOpTools workbench. These objects may not\n"
        "function correctly with the installed version.\n\n"
        f"{entries}\n\n"
        "Ray propagation is disabled until you update to the latest version\n"
        "of the pyOpTools workbench.\n"
        "Saving this document may result in incomplete or incorrect data\n"
        "for the affected objects."
    )

    _wrn(msg + "\n")

    from PySide import QtCore, QtWidgets

    msg_box = QtWidgets.QMessageBox()
    msg_box.setWindowTitle("pyoptools - Forward Version Warning")
    msg_box.setIcon(QtWidgets.QMessageBox.Warning)
    msg_box.setText(msg)
    ok_btn = msg_box.addButton("OK", QtWidgets.QMessageBox.AcceptRole)
    msg_box.exec_()

    _forward_warn_accumulator = []



class WBPart:
    """Base object for all FreeCAD pyOpTools optical parts.

    This class handles all the common behaviour of optical parts in the workbench.

    Class Attributes
    ----------------
    CURRENT_BASE_VERSION : int
        Tracks the current base class schema version. Used to auto-set
        ``obj.BaseVersion`` in ``__init__`` and to detect forward incompatibility
        in ``onDocumentRestored``. Must be incremented when the base class
        schema changes (e.g., adding/removing base properties).

    CURRENT_PART_VERSION : int
        Tracks the current part-specific schema version. Every child class
        **must** define its own ``CURRENT_PART_VERSION`` (enforced by
        ``__init_subclass__``). There is no default on WBPart — forgetting
        to define it raises ``TypeError`` at import time. Set to 0 for
        initial/unversioned objects, and increment when the object schema
        changes.

    Properties
    ----------
    Enabled : bool
        Indicates if the current optical part is enabled. When disabled,
        the part is ignored from optical calculations.

    Notes : str
        Text field for custom user annotations.

    Reference : str
        Field to save the optical part supplier reference.

    Forward-Version Safeguard
    ------------------------
    When a .FCStd file created with a NEWER version of the workbench is
    opened with an OLDER version, ``onDocumentRestored`` detects the version
    mismatch and accumulates per-object warnings. A persistent
    ``QTimer`` is started (or restarted) on each detection; it fires 300ms
    after the last warning, showing a single consolidated popup with all
    forward-incompatible objects. This ensures the dialog appears only
    after all objects have been restored.

    Simulation blocking is enforced in ``propagate.py`` — ray propagation
    is completely blocked when any forward-incompatible object exists.

    The warning popup also notes that saving the document may result in
    incomplete or incorrect data for the affected objects.

    Version History
    --------------
    Version 1:
    - Renamed 'cType' to 'ComponentType'
    - Added 'BaseSeVersion' attribute to track WBPart class versions
    - Added 'ObjectVersion' attribute to track WBPart child class versions
    - Renamed 'enabled' to 'Enabled' to follow FreeCAD naming convention

    Version 0:
    - Initial version
    """

    CURRENT_BASE_VERSION = 1

    def __init_subclass__(cls, **kwargs):
        if "CURRENT_PART_VERSION" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} must define CURRENT_PART_VERSION as a class attribute. "
                f"Set CURRENT_PART_VERSION = 0 for initial/unversioned objects, "
                f"and increment it when the object schema changes."
            )
        if not isinstance(cls.CURRENT_PART_VERSION, int) or cls.CURRENT_PART_VERSION < 0:
            raise TypeError(
                f"{cls.__name__}.CURRENT_PART_VERSION must be a non-negative integer, "
                f"got {type(cls.CURRENT_PART_VERSION).__name__}: {cls.CURRENT_PART_VERSION!r}"
            )

    def __init__(self, obj, PartType, enabled=True, reference="", notes=""):
        obj.Proxy = self
        obj.addProperty("App::PropertyBool", "Enabled").Enabled = enabled
        obj.addProperty("App::PropertyString", "Reference").Reference = reference
        obj.addProperty("App::PropertyString", "Notes").Notes = notes

        obj.addProperty(
            "App::PropertyString", "ComponentType", "Base", "pyOpTools Component Type"
        ).ComponentType = PartType
        obj.setEditorMode("ComponentType", 1)  # 1 Read-Only

        obj.addProperty(
            "App::PropertyInteger",
            "BaseVersion",
            "Versioning",
            "Version of the base class",
        ).BaseVersion = WBPart.CURRENT_BASE_VERSION
        obj.setEditorMode("BaseVersion", 1)  # 1 Read-Only

        # Auto-set ObjectVersion from the child class's CURRENT_PART_VERSION.
        # type(self) resolves to the actual child class at runtime.
        obj.addProperty(
            "App::PropertyInteger",
            "ObjectVersion",
            "Versioning",
            "Version of the actual object",
        ).ObjectVersion = type(self).CURRENT_PART_VERSION
        obj.setEditorMode("ObjectVersion", 1)  # 1 Read-Only

    def onDocumentRestored(self, obj):
        """
        Handles the migration of objects when a document is restored.

        This method ensures that objects are properly migrated during the document restore process.
        If this method is overridden in any subclasses, ensure that `WBPart.onDocumentRestored`
        is called to maintain base behavior.

        :param obj: The specific FreeCAD object that is being restored.
        """

        # Verify what migration must be applied, make sure to use if and not elif to assure
        # all the migrations are executed sequentially.

        # Current base object is in version 0
        if not hasattr(obj, "BaseVersion"):
            migrate_to_v1(obj)

        # Forward-version safeguard: detect when file was created with newer code
        _obj_warnings = []

        if hasattr(obj, "BaseVersion") and obj.BaseVersion > WBPart.CURRENT_BASE_VERSION:
            _obj_warnings.append(
                f"base: v{obj.BaseVersion}, installed: v{WBPart.CURRENT_BASE_VERSION}"
            )

        if (
            hasattr(obj, "ObjectVersion")
            and hasattr(type(self), "CURRENT_PART_VERSION")
            and obj.ObjectVersion > type(self).CURRENT_PART_VERSION
        ):
            _obj_warnings.append(
                f"object: v{obj.ObjectVersion}, installed: v{type(self).CURRENT_PART_VERSION}"
            )

        if _obj_warnings:
            _wrn(
                f'Forward incompatibility: "{obj.Label}" ({type(self).__name__}) was saved with a newer\n'
                f'version of the pyOpTools workbench ({"; ".join(_obj_warnings)}) but the\n'
                f'installed workbench is older\n'
            )

            global _forward_warn_accumulator, _forward_warn_timer

            _entry = f'  - "{obj.Label}" ({type(self).__name__})'
            _forward_warn_accumulator.append(_entry)

            # Schedule/restart a consolidated popup 300ms after the last
            # forward-incompatible object is detected. Each call to start()
            # restarts the countdown, so the popup only fires after all
            # onDocumentRestored calls have completed.
            from PySide import QtCore

            if _forward_warn_timer is None:
                _forward_warn_timer = QtCore.QTimer()
                _forward_warn_timer.setSingleShot(True)
                _forward_warn_timer.timeout.connect(_show_forward_version_popup)
            _forward_warn_timer.start(300)

    def onChanged(self, obj, prop):
        """
        Responds to changes in the object's properties.

        This method is triggered whenever a property of the object changes.
        Specifically, if the "Enabled" property changes, it adjusts the
        object's transparency. If this method is overloaded, the overloading
        method must ensure that the `WBPart.onChanged` method is called to
        maintain base behavior and functionality.

        Parameters
        ----------
        obj : object
            The FreeCAD object whose property has changed.

        prop : str
            The name of the property that has changed.
        """
        if prop == "Enabled":
            if obj.Enabled:
                obj.ViewObject.Transparency = 30
            else:
                obj.ViewObject.Transparency = 90

    def pyoptools_repr(self, obj):
        print(
            f"pyOpTools representation of Object {self.pyOpToolsType} not implemented"
        )


def migrate_to_v1(obj):
    
    obj.addProperty(
        "App::PropertyInteger",
        "BaseVersion",
        "Versioning",
        "Version of the base class",
    ).BaseVersion = 1
    obj.setEditorMode("BaseVersion", 1)  # 1 Read-Only

    # Each object must update its object_version to its real value.
    obj.addProperty(
        "App::PropertyInteger",
        "ObjectVersion",
        "Versioning",
        "Version of the actual object",
    ).ObjectVersion = 0
    obj.setEditorMode("ObjectVersion", 1)  # 1 Read-Only

    # Rename the ComponentType attribute and remove it
    obj.addProperty(
        "App::PropertyString", "ComponentType", "Base", "pyOpTools Component Type"
    ).ComponentType = obj.cType
    obj.setEditorMode("ComponentType", 1)  # 1 Read-Only

    obj.removeProperty("cType")

    # Rename enabled to Enabled

    obj.addProperty("App::PropertyBool", "Enabled").Enabled = obj.enabled
    obj.removeProperty("enabled")

    _wrn(f"Migrating base object of {obj.ComponentType} from v0 to v1\n")
