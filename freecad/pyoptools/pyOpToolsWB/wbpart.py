import FreeCAD

_wrn = FreeCAD.Console.PrintWarning


class WBPart:
    """Base object for all FreeCAD pyOpTools optical parts.

    This class handles all the common behaviour of optical parts in the workbench.

    Properties
    ----------
    Enabled : bool
        Indicates if the current optical part is enabled. When disabled,
        the part is ignored from optical calculations.

    Notes : str
        Text field for custom user annotations.

    Reference : str
        Field to save the optical part supplier reference.

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

    def __init__(self, obj, PartType, enabled=True, reference="", notes=""):
        obj.Proxy = self
        obj.addProperty("App::PropertyBool", "Enabled").Enabled = enabled
        obj.addProperty("App::PropertyString", "Reference").Reference = reference
        obj.addProperty("App::PropertyString", "Notes").Notes = notes

        obj.addProperty(
            "App::PropertyString", "ComponentType", "Base", "pyOpTools Component Type"
        ).ComponentType = PartType
        obj.setEditorMode("ComponentType", 1)  # 1 Read-Only

        obj.addProperty("App::PropertyInteger", "BaseVersion").BaseVersion = 1
        obj.setEditorMode("BaseVersion", 1)  # 1 Read-Only

        # Each object must update its object_version to its real value.
        obj.addProperty("App::PropertyInteger", "ObjectVersion").ObjectVersion = 0
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
    # Create BaseVersion and ObjectVesrion properties, and set the current base version.
    obj.addProperty("App::PropertyInteger", "BaseVersion").BaseVersion = 1
    obj.setEditorMode("BaseVersion", 1)  # 1 Read-Only

    # Before this, Objects where unversioned
    obj.addProperty("App::PropertyInteger", "ObjectVersion").ObjectVersion = 0
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

    _wrn("Migrating base object from v0 to v1\n")
