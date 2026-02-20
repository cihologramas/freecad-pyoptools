# -*- coding: utf-8 -*-
"""Sensors Panel - Dockable widget for managing sensors."""

import FreeCAD
import FreeCADGui as Gui
from PySide import QtWidgets, QtCore


class SensorsPanel(QtWidgets.QDockWidget):
    """Dockable panel for managing all sensors in the document."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensors")
        
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
        
        # Table for sensors
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
        self.info_label = QtWidgets.QLabel("No sensors in document")
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
        self.refresh_sensors()
        
        # Set up document observer for auto-refresh
        self.setup_observers()
    
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
        # Check if ComponentType was just set to Sensor (new object)
        if prop == "ComponentType" and hasattr(obj, "ComponentType"):
            if obj.ComponentType == "Sensor":
                # New sensor created - do full refresh
                self.refresh_sensors()
                return
        
        # Check if it's a sensor and a relevant property changed
        if (hasattr(obj, "ComponentType") and 
            obj.ComponentType == "Sensor" and
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
                
                # Update Notes (column 2)
                elif prop == "Notes":
                    notes_item = self.table.item(row, 2)
                    if notes_item:
                        notes_text = obj.Notes if hasattr(obj, "Notes") and obj.Notes else ""
                        notes_item.setText(notes_text)
    
    def slotCreatedObject(self, obj):
        """Called when a new object is created in the document."""
        # Check if it's a sensor
        if hasattr(obj, "ComponentType") and obj.ComponentType == "Sensor":
            # Refresh the entire list
            self.refresh_sensors()
    
    def slotDeletedObject(self, obj):
        """Called when an object is deleted from the document."""
        # Check if it's a sensor
        if hasattr(obj, "ComponentType") and obj.ComponentType == "Sensor":
            # Refresh the entire list
            self.refresh_sensors()
    
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
    
    def refresh_sensors(self):
        """Refresh the list of sensors from the active document."""
        doc = FreeCAD.ActiveDocument
        if not doc:
            self.table.setRowCount(0)
            self.row_objects = []
            self.info_label.setText("No active document")
            self.info_label.setVisible(True)
            self.btn_enable_all.setEnabled(False)
            self.btn_disable_all.setEnabled(False)
            return
        
        # Find all sensors
        sensors = [
            obj for obj in doc.Objects
            if hasattr(obj, "ComponentType") and 
            obj.ComponentType == "Sensor"
        ]
        
        if not sensors:
            self.table.setRowCount(0)
            self.row_objects = []
            self.info_label.setText("No sensors in document")
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
        self.table.setRowCount(len(sensors))
        self.row_objects = sensors
        
        for i, obj in enumerate(sensors):
            # Column 0: Enabled checkbox
            checkbox = QtWidgets.QCheckBox()
            # Block signals while setting initial state to avoid false triggers
            checkbox.blockSignals(True)
            checkbox.setChecked(obj.Enabled if hasattr(obj, "Enabled") else True)
            checkbox.blockSignals(False)
            # Connect after setting initial state
            checkbox.stateChanged.connect(
                lambda state, o=obj: self.toggle_sensor(o, state)
            )
            checkbox_widget = QtWidgets.QWidget()
            checkbox_layout = QtWidgets.QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(QtCore.Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 0, checkbox_widget)
            
            # Column 1: Label
            label_item = QtWidgets.QTableWidgetItem(obj.Label)
            label_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
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
    
    def toggle_sensor(self, obj, state):
        """Toggle enabled state of a sensor."""
        if not hasattr(obj, "Enabled"):
            return
        
        # Check if checkbox is checked
        if state == QtCore.Qt.Checked.value:
            obj.Enabled = True
            FreeCAD.Console.PrintMessage(f"Sensor '{obj.Label}' enabled\n")
        else:
            obj.Enabled = False
            FreeCAD.Console.PrintMessage(f"Sensor '{obj.Label}' disabled\n")
        
        # Mark object as touched to trigger update
        obj.touch()
        
        # Recompute document
        if FreeCAD.ActiveDocument:
            FreeCAD.ActiveDocument.recompute()
    
    def enable_all(self):
        """Enable all sensors."""
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
        self.refresh_sensors()
        FreeCAD.Console.PrintMessage(f"Enabled {count} sensor(s)\n")
    
    def disable_all(self):
        """Disable all sensors."""
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
        self.refresh_sensors()
        FreeCAD.Console.PrintMessage(f"Disabled {count} sensor(s)\n")
    
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
