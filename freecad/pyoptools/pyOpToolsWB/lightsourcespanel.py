# -*- coding: utf-8 -*-
"""Light Sources Panel - Dockable widget for managing light sources."""

import os
import FreeCAD
import FreeCADGui as Gui
from PySide import QtWidgets, QtCore, QtGui
from pyoptools.misc.pmisc.misc import wavelength2RGB


class LightSourcesPanel(QtWidgets.QDockWidget):
    """Dockable panel for managing all light sources in the document."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Light Sources")
        
        # Initialize caches before creating icons
        self._icon_cache = {}
        self._svg_templates = {}
        
        # Create icons for different light source types
        self._type_icons = self._create_type_icons()
        
        # Allow docking on left or right only
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        
        # Allow closing, moving, and floating
        self.setFeatures(
            QtWidgets.QDockWidget.DockWidgetClosable |
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        
        # Set minimum width for compact layout
        self.setMinimumWidth(220)
        
        # Main widget
        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # Table for light sources
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["En", "Label", "Notes"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        # Set column widths - compact layout
        self.table.setColumnWidth(0, 35)  # Enabled checkbox - minimal width
        self.table.setColumnWidth(1, 60)  # Label - for ~6 characters
        self.table.horizontalHeader().setStretchLastSection(True)  # Notes stretches
        
        # Connect selection change
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        
        layout.addWidget(self.table)
        
        # Button bar
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(6)
        
        self.btn_enable_all = QtWidgets.QPushButton("Enable All")
        self.btn_disable_all = QtWidgets.QPushButton("Disable All")
        
        self.btn_enable_all.clicked.connect(self.enable_all)
        self.btn_disable_all.clicked.connect(self.disable_all)
        
        btn_layout.addWidget(self.btn_enable_all)
        btn_layout.addWidget(self.btn_disable_all)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Info label
        self.info_label = QtWidgets.QLabel("No light sources in document")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        main_widget.setLayout(layout)
        self.setWidget(main_widget)
        
        # Track if we're updating from FreeCAD selection (prevent recursion)
        self._updating_from_freecad = False
        self._updating_from_table = False
        
        # Store object references for each row
        self.row_objects = []
        
        # Initial population
        self.refresh_sources()
        
        # Set up document observer for auto-refresh
        self.setup_observers()
    
    def _create_type_icons(self):
        """Load SVG templates for each light source type from resources folder."""
        # Get the path to the resources directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resources_dir = os.path.join(os.path.dirname(current_dir), "resources")
        
        # Map component types to their SVG template files
        icon_files = {
            "RaysPoint": "rayspoint.svg",
            "RaysPar": "rayspar.svg",
            "RaysArray": "raysarray.svg",
            "Ray": "ray.svg"
        }
        
        # Load SVG templates as text for dynamic color replacement
        for type_name, filename in icon_files.items():
            svg_path = os.path.join(resources_dir, filename)
            if os.path.exists(svg_path):
                with open(svg_path, 'r') as f:
                    self._svg_templates[type_name] = f.read()
        
        # Return empty dict - icons will be generated per-object based on wavelength
        return {}
    
    def _get_wavelength_from_object(self, obj):
        """Extract wavelength in micrometers from a light source object."""
        # Different ray types use different property names
        if hasattr(obj, "wl"):  # Ray, RaysPoint, RaysPar
            return obj.wl.getValueAs("µm").Value
        elif hasattr(obj, "wavelength"):  # RaysArray
            return obj.wavelength / 1000.0  # Convert nm to µm
        return 0.633  # Default 633nm in µm
    
    def _create_icon_for_object(self, obj):
        """Create a wavelength-colored icon for a specific object."""
        component_type = obj.ComponentType
        
        # Get SVG template
        svg_template = self._svg_templates.get(component_type)
        if not svg_template:
            return QtGui.QIcon()  # Return empty icon if no template
        
        # Get wavelength and convert to RGB
        wavelength_um = self._get_wavelength_from_object(obj)
        r, g, b = wavelength2RGB(wavelength_um)
        
        # Convert to hex color
        color_hex = "#{:02x}{:02x}{:02x}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )
        darker_hex = "#{:02x}{:02x}{:02x}".format(
            int(r * 180), int(g * 180), int(b * 180)  # Darker for stroke
        )
        
        # Replace standard gray colors with wavelength colors
        svg_colored = svg_template.replace("#808080", color_hex)
        svg_colored = svg_colored.replace("#606060", darker_hex)
        
        # Render SVG to icon
        return self._svg_to_icon(svg_colored)
    
    def _svg_to_icon(self, svg_data):
        """Convert SVG string data to QIcon."""
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        try:
            from PySide import QtSvg
            renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg_data.encode('utf-8')))
            renderer.render(painter)
        except ImportError:
            # Fallback: create a simple colored circle
            painter.setBrush(QtGui.QBrush(QtGui.QColor(150, 150, 150)))
            painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100), 1))
            painter.drawEllipse(2, 2, 12, 12)
        
        painter.end()
        return QtGui.QIcon(pixmap)
    
    def get_icon_for_type(self, component_type):
        """Get icon for a specific component type."""
        # Legacy method - no longer used since icons are per-object
        return QtGui.QIcon()
    
    def setup_observers(self):
        """Set up observers to auto-refresh when document changes."""
        # Connect to FreeCAD's selection observer
        if hasattr(Gui, 'Selection'):
            Gui.Selection.addObserver(self)
        
        # Register as document observer for auto-refresh
        FreeCAD.addDocumentObserver(self)
    
    def addSelection(self, doc, obj, sub, pnt):
        """Called when object is selected in FreeCAD."""
        self.sync_selection_from_freecad()
    
    def removeSelection(self, doc, obj, sub):
        """Called when object is deselected in FreeCAD."""
        self.sync_selection_from_freecad()
    
    def clearSelection(self, doc):
        """Called when selection is cleared in FreeCAD."""
        self.sync_selection_from_freecad()
    
    def slotChangedObject(self, obj, prop):
        """Called when an object property changes (document observer callback)."""
        # Check if ComponentType was just set to a light source type (new object)
        if prop == "ComponentType" and hasattr(obj, "ComponentType"):
            if obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]:
                # New light source created - do full refresh
                self.refresh_sources()
                return
        
        # Check if wavelength changed - invalidate icon cache and update
        if prop in ["wl", "wavelength"]:
            if hasattr(obj, "ComponentType") and obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]:
                # Clear cached icon for this object
                obj_id = id(obj)
                if obj_id in self._icon_cache:
                    del self._icon_cache[obj_id]
                
                # Update the icon in the table
                if obj in self.row_objects:
                    row = self.row_objects.index(obj)
                    label_item = self.table.item(row, 1)
                    if label_item:
                        icon = self._get_cached_icon(obj)
                        label_item.setIcon(icon)
                return
        
        # Check if it's a light source and a relevant property changed
        if (hasattr(obj, "ComponentType") and 
            obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"] and
            prop in ["Enabled", "Label", "Notes"]):
            
            # Update the corresponding row
            if obj in self.row_objects:
                row = self.row_objects.index(obj)
                
                # Update Enabled checkbox (column 0)
                if prop == "Enabled":
                    checkbox_widget = self.table.cellWidget(row, 0)
                    if checkbox_widget:
                        checkbox = checkbox_widget.findChild(QtWidgets.QCheckBox)
                        if checkbox:
                            checkbox.blockSignals(True)
                            checkbox.setChecked(obj.Enabled)
                            checkbox.blockSignals(False)
                
                # Update Label (column 1)
                elif prop == "Label":
                    label_item = self.table.item(row, 1)
                    if label_item:
                        label_item.setText(obj.Label)
                        # Preserve the icon
                        icon = self._get_cached_icon(obj)
                        label_item.setIcon(icon)
                
                # Update Notes (column 2)
                elif prop == "Notes":
                    notes_item = self.table.item(row, 2)
                    if notes_item:
                        notes_text = obj.Notes if hasattr(obj, "Notes") and obj.Notes else ""
                        notes_item.setText(notes_text)
    
    def slotCreatedObject(self, obj):
        """Called when a new object is created in the document."""
        # Check if it's a light source
        if hasattr(obj, "ComponentType") and obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]:
            # Refresh the entire list
            self.refresh_sources()
    
    def slotDeletedObject(self, obj):
        """Called when an object is deleted from the document."""
        # Check if it's a light source
        if hasattr(obj, "ComponentType") and obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]:
            # Refresh the entire list
            self.refresh_sources()
    
    def sync_selection_from_freecad(self):
        """Synchronize table selection from FreeCAD selection."""
        if self._updating_from_table:
            return
        
        self._updating_from_freecad = True
        try:
            selected_objs = Gui.Selection.getSelection()
            
            # Clear table selection
            self.table.clearSelection()
            
            # Select matching rows in table
            for i, obj in enumerate(self.row_objects):
                if obj in selected_objs:
                    self.table.selectRow(i)
        finally:
            self._updating_from_freecad = False
    
    def on_table_selection_changed(self):
        """Handle table selection change - update FreeCAD selection."""
        if self._updating_from_freecad:
            return
        
        self._updating_from_table = True
        try:
            # Get selected rows
            selected_rows = set()
            for item in self.table.selectedItems():
                selected_rows.add(item.row())
            
            # Clear FreeCAD selection
            Gui.Selection.clearSelection()
            
            # Select corresponding objects
            for row in selected_rows:
                if row < len(self.row_objects):
                    obj = self.row_objects[row]
                    Gui.Selection.addSelection(obj)
        finally:
            self._updating_from_table = False
    
    def _get_cached_icon(self, obj):
        """Get or create a cached icon for an object."""
        obj_id = id(obj)
        if obj_id not in self._icon_cache:
            self._icon_cache[obj_id] = self._create_icon_for_object(obj)
        return self._icon_cache[obj_id]
    
    def refresh_sources(self):
        """Refresh the list of light sources from the active document."""
        doc = FreeCAD.ActiveDocument
        if not doc:
            self.table.setRowCount(0)
            self.row_objects = []
            self.info_label.setText("No active document")
            self.info_label.setVisible(True)
            self.btn_enable_all.setEnabled(False)
            self.btn_disable_all.setEnabled(False)
            return
        
        # Find all light sources
        sources = [
            obj for obj in doc.Objects
            if hasattr(obj, "ComponentType") and 
            obj.ComponentType in ["RaysPoint", "RaysPar", "RaysArray", "Ray"]
        ]
        
        if not sources:
            self.table.setRowCount(0)
            self.row_objects = []
            self.info_label.setText("No light sources in document")
            self.info_label.setVisible(True)
            self.btn_enable_all.setEnabled(False)
            self.btn_disable_all.setEnabled(False)
            return
        
        # Update info label
        self.info_label.setVisible(False)
        self.btn_enable_all.setEnabled(True)
        self.btn_disable_all.setEnabled(True)
        
        # Block signals during update
        self.table.blockSignals(True)
        
        # Update table
        self.table.setRowCount(len(sources))
        self.row_objects = sources
        
        for i, obj in enumerate(sources):
            # Column 0: Enabled checkbox
            checkbox = QtWidgets.QCheckBox()
            # Block signals while setting initial state to avoid false triggers
            checkbox.blockSignals(True)
            checkbox.setChecked(obj.Enabled if hasattr(obj, "Enabled") else True)
            checkbox.blockSignals(False)
            # Connect after setting initial state
            checkbox.stateChanged.connect(
                lambda state, o=obj: self.toggle_source(o, state)
            )
            checkbox_widget = QtWidgets.QWidget()
            checkbox_layout = QtWidgets.QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(QtCore.Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 0, checkbox_widget)
            
            # Column 1: Label with wavelength-colored icon
            label_item = QtWidgets.QTableWidgetItem(obj.Label)
            label_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            # Set icon based on component type and wavelength
            icon = self._get_cached_icon(obj)
            label_item.setIcon(icon)
            self.table.setItem(i, 1, label_item)
            
            # Column 2: Notes
            notes_text = obj.Notes if hasattr(obj, "Notes") and obj.Notes else ""
            notes_item = QtWidgets.QTableWidgetItem(notes_text)
            notes_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.table.setItem(i, 2, notes_item)
        
        # Restore signals
        self.table.blockSignals(False)
        
        # Sync selection from FreeCAD
        self.sync_selection_from_freecad()
    
    def toggle_source(self, obj, state):
        """Toggle enabled state of a light source."""
        if not hasattr(obj, "Enabled"):
            return
        
        # Check if checkbox is checked
        if state == QtCore.Qt.Checked.value:
            obj.Enabled = True
            FreeCAD.Console.PrintMessage(f"Light source '{obj.Label}' enabled\n")
        else:
            obj.Enabled = False
            FreeCAD.Console.PrintMessage(f"Light source '{obj.Label}' disabled\n")
        
        # Mark object as touched to trigger update
        obj.touch()
        
        # Recompute document
        if FreeCAD.ActiveDocument:
            FreeCAD.ActiveDocument.recompute()
    
    def enable_all(self):
        """Enable all light sources."""
        doc = FreeCAD.ActiveDocument
        if not doc:
            return
        
        count = 0
        for obj in self.row_objects:
            if hasattr(obj, "Enabled"):
                obj.Enabled = True
                obj.touch()
                count += 1
        
        doc.recompute()
        self.refresh_sources()
        FreeCAD.Console.PrintMessage(f"Enabled {count} light source(s)\n")
    
    def disable_all(self):
        """Disable all light sources."""
        doc = FreeCAD.ActiveDocument
        if not doc:
            return
        
        count = 0
        for obj in self.row_objects:
            if hasattr(obj, "Enabled"):
                obj.Enabled = False
                obj.touch()
                count += 1
        
        doc.recompute()
        self.refresh_sources()
        FreeCAD.Console.PrintMessage(f"Disabled {count} light source(s)\n")
    
    def closeEvent(self, event):
        """Handle panel close event."""
        # Remove selection observer
        if hasattr(Gui, 'Selection'):
            try:
                Gui.Selection.removeObserver(self)
            except:
                pass
        
        # Remove document observer
        try:
            FreeCAD.removeDocumentObserver(self)
        except:
            pass
        
        super().closeEvent(event)
