import FreeCADGui
from PySide import QtCore, QtGui, QtWidgets
from freecad.pyoptools.pyOpToolsWB.qthelpers import getUIFilePath
from freecad.pyoptools.pyOpToolsWB.selectionhelpers import SelectionObserver
import FreeCAD
import Part
import math


# Legacy classes removed - now using modern SelectionObserver pattern from selectionhelpers.py


def isLine(edge):
    """Check if edge is a straight line."""
    if not hasattr(edge, "Curve"):
        return False
    return isinstance(edge.Curve, Part.Line)


def isCircleOrArc(edge):
    """Check if edge is a circle or arc."""
    if not hasattr(edge, "Curve"):
        return False
    return isinstance(edge.Curve, (Part.Circle, Part.ArcOfCircle))


def isValidCurveForCapture(edge):
    """Check if edge is valid for position/orientation capture (line, circle, or arc)."""
    return isLine(edge) or isCircleOrArc(edge)


def isValidFaceForCapture(face):
    """Check if face is valid for position/orientation capture.
    
    Accepts planar faces (flat surfaces) and cylindrical/conical surfaces.
    """
    if not hasattr(face, "Surface"):
        return False
    
    surface = face.Surface
    # Accept planar faces (flat surfaces like mirrors, rectangular surfaces)
    if isinstance(surface, Part.Plane):
        return True
    # Accept cylindrical faces (lens surfaces)
    if isinstance(surface, (Part.Cylinder, Part.Cone, Part.Sphere, Part.Toroid)):
        return True
    
    return False


# EventLogger class removed - no longer needed with SelectionObserver pattern


class placementWidget(QtWidgets.QWidget):
    def __init__(self):
        super(placementWidget, self).__init__()
        self.initUI()
        self.position_observer = None
        self.orientation_observer = None

    def initUI(self):
        fn1 = getUIFilePath("positionWidget.ui")
        self.ui = FreeCADGui.PySideUic.loadUi(fn1, self)
        self.setLayout(self.ui.mainLayout)

        # Connect buttons to new pick methods
        self.ui.posCap.toggled.connect(self.getPosition)
        self.ui.orienCap.toggled.connect(self.getOrientation)
        
        # Setup button icons
        self._setupPickButtonIcons()

    def hideEvent(self, event):
        event.accept()  # let the window close
        self.stopAllPicking()
    
    def _setupPickButtonIcons(self):
        """Setup icons for pick buttons to match positiononray.py style."""
        try:
            from freecad.pyoptools import ICONPATH
            import os
            
            icon_path = os.path.join(ICONPATH, "pick-from-view.svg")
            if os.path.exists(icon_path):
                icon = QtGui.QIcon(icon_path)
                self.ui.posCap.setIcon(icon)
                self.ui.orienCap.setIcon(icon)
                self.ui.posCap.setIconSize(QtCore.QSize(16, 16))
                self.ui.orienCap.setIconSize(QtCore.QSize(16, 16))
        except Exception as e:
            # If icon loading fails, buttons will just show without icon
            FreeCAD.Console.PrintLog(f"Could not load pick button icons: {e}\n")
    
    def stopAllPicking(self):
        """Stop all active picking operations."""
        self.stopPositionPick()
        self.stopOrientationPick()

    def getPosition(self, checked):
        """Handle position capture button toggle."""
        if checked:
            # Stop orientation picking if active
            self.ui.orienCap.setChecked(False)
            self.stopOrientationPick()
            # Start position picking
            self.startPositionPick()
        else:
            self.stopPositionPick()

    def getOrientation(self, checked):
        """Handle orientation capture button toggle."""
        if checked:
            # Stop position picking if active
            self.ui.posCap.setChecked(False)
            self.stopPositionPick()
            # Start orientation picking
            self.startOrientationPick()
        else:
            self.stopOrientationPick()

    # === Position Picking Methods (Modern SelectionObserver Pattern) ===
    
    def startPositionPick(self):
        """Start picking mode for position capture."""
        if self.position_observer is not None:
            return  # Already picking
        
        # Create observer
        self.position_observer = SelectionObserver(
            callback=self.onPositionEdgePicked,
            filter_func=self.isValidSelectionForCapture,
            error_message="Please select an edge or face on an optical component"
        )
        FreeCADGui.Selection.addObserver(self.position_observer)
        
        # Visual feedback
        FreeCAD.Console.PrintMessage("Click on edge in 3D view to capture position\n")
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)
    
    def stopPositionPick(self):
        """Stop position picking mode."""
        if self.position_observer is not None:
            FreeCADGui.Selection.removeObserver(self.position_observer)
            self.position_observer = None
            QtGui.QApplication.restoreOverrideCursor()
    
    def onPositionEdgePicked(self, obj, sub):
        """Callback when valid edge or face picked for position.
        
        Args:
            obj: FreeCAD object containing the edge/face
            sub: Sub-element string (e.g., "Edge1", "Face1")
        """
        try:
            element = obj.Shape.getElement(sub)
            
            # Determine snap point based on element type
            if sub.startswith("Face"):
                # For faces, use center of mass (works for flat and curved surfaces)
                snap_point = element.CenterOfMass
            elif isCircleOrArc(element):
                # For circular/arc edges, use the center point
                snap_point = element.Curve.Center
            else:
                # For line edges, use first endpoint
                snap_point = element.Vertexes[0].Point
            
            # Update UI
            self.ui.X.setValue(snap_point.x)
            self.ui.Y.setValue(snap_point.y)
            self.ui.Z.setValue(snap_point.z)
            
            # Uncheck button and cleanup
            self.ui.posCap.setChecked(False)
            FreeCADGui.Selection.clearSelection()
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error capturing position: {e}\n")
    
    # === Orientation Picking Methods ===
    
    def startOrientationPick(self):
        """Start picking mode for orientation capture."""
        if self.orientation_observer is not None:
            return  # Already picking
        
        # Create observer
        self.orientation_observer = SelectionObserver(
            callback=self.onOrientationEdgePicked,
            filter_func=self.isValidSelectionForCapture,
            error_message="Please select an edge or face on an optical component"
        )
        FreeCADGui.Selection.addObserver(self.orientation_observer)
        
        # Visual feedback
        FreeCAD.Console.PrintMessage("Click on edge in 3D view to capture orientation\n")
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.CrossCursor)
    
    def stopOrientationPick(self):
        """Stop orientation picking mode."""
        if self.orientation_observer is not None:
            FreeCADGui.Selection.removeObserver(self.orientation_observer)
            self.orientation_observer = None
            QtGui.QApplication.restoreOverrideCursor()
    
    def onOrientationEdgePicked(self, obj, sub):
        """Callback when valid edge or face picked for orientation.
        
        Args:
            obj: FreeCAD object containing the edge/face
            sub: Sub-element string (e.g., "Edge1", "Face1")
        """
        try:
            element = obj.Shape.getElement(sub)
            
            # Get direction vector based on element type
            if sub.startswith("Face"):
                # For faces, use the surface normal at center
                # Get the normal vector from the surface
                if hasattr(element.Surface, 'Axis'):
                    # Cylindrical, spherical surfaces have an axis
                    direction = element.Surface.Axis
                else:
                    # For planar faces, get normal from the plane
                    u_mid = (element.ParameterRange[0] + element.ParameterRange[1]) / 2
                    v_mid = (element.ParameterRange[2] + element.ParameterRange[3]) / 2
                    direction = element.normalAt(u_mid, v_mid)
            elif isCircleOrArc(element):
                # For circles/arcs, use the normal vector of the circle plane
                direction = element.Curve.Axis
            else:
                # For lines, use the direction from vertex to vertex
                p0 = element.Vertexes[0].Point
                p1 = element.Vertexes[1].Point
                direction = (p1 - p0).normalize()
            
            # Convert direction vector to Euler angles (simplified approach)
            # This gives rotation that would align Z-axis with the edge direction
            rx = math.degrees(math.atan2(direction.y, direction.z))
            ry = math.degrees(math.atan2(-direction.x, math.sqrt(direction.y**2 + direction.z**2)))
            rz = 0  # No roll component in this simple calculation
            
            # Update UI
            self.ui.RX.setValue(rx)
            self.ui.RY.setValue(ry)
            self.ui.RZ.setValue(rz)
            
            # Uncheck button and cleanup
            self.ui.orienCap.setChecked(False)
            FreeCADGui.Selection.clearSelection()
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error capturing orientation: {e}\n")
    
    # === Validation Methods ===
    
    def isValidSelectionForCapture(self, obj, sub):
        """Validate that selection is a valid edge or face on an optical component.
        
        Args:
            obj: FreeCAD object
            sub: Sub-element string (e.g., "Edge1", "Face1")
        
        Returns:
            bool: True if valid for capture
        """
        # Must be an optical component
        if not hasattr(obj, "ComponentType"):
            return False
        
        # Must select an edge or face
        if not sub:
            return False
        
        # Check if it's a valid edge or face
        try:
            element = obj.Shape.getElement(sub)
            
            if sub.startswith("Edge"):
                return isValidCurveForCapture(element)
            elif sub.startswith("Face"):
                return isValidFaceForCapture(element)
            else:
                return False
        except Exception:
            return False

    @property
    def Xpos(self):
        return self.ui.X

    @property
    def Ypos(self):
        return self.ui.Y

    @property
    def Zpos(self):
        return self.ui.Z

    @property
    def Xrot(self):
        return self.ui.RX

    @property
    def Yrot(self):
        return self.ui.RY

    @property
    def Zrot(self):
        return self.ui.RZ
