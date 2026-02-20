# -*- coding: utf-8 -*-
"""Classes used to define a component from different catalogs."""

import FreeCAD
import FreeCADGui
from .wbcommand import WBCommandGUI, WBCommandMenu, WBPart
from .feedback import FeedbackHelper
from freecad.pyoptools.pyOpToolsWB.widgets.placementWidget import placementWidget
from PySide import QtCore, QtGui, QtWidgets
from pyoptools.raytrace.library import library
from pyoptools.raytrace.mat_lib import material
from .sphericallens import InsertSL
from .doubletlens import InsertDL
from .cylindricallens import InsertCL
from .component_info_formatter import ComponentInfoFormatter
from math import radians


class CatalogComponentGUI(WBCommandGUI):
    @FeedbackHelper.with_busy_cursor
    def __init__(self):
        pw = placementWidget()
        WBCommandGUI.__init__(self, [pw, "CatalogComponent.ui"])

        # Store all catalog names for later use
        self.all_catalog_names = list(library.catalogs())

        # Cache catalog objects to avoid reloading JSON each time
        self._catalog_cache = {}
        for cat_name in self.all_catalog_names:
            self._catalog_cache[cat_name] = getattr(library, cat_name)

        # Cache catalog parts lists (sorted) to avoid repeated work
        self._catalog_parts_cache = {}

        # Catalog selection state:
        # - "All Catalogs" is a mode flag used to scope searches
        # - Individual catalogs are represented by checked items in the combobox model
        self._all_catalogs_mode = False

        # Configure catalog dropdown for checkable items + custom display text
        self.form.Catalog.setEditable(True)
        self.form.Catalog.lineEdit().setReadOnly(True)

        # Replace model with a standard item model so we can use check states
        cat_model = QtGui.QStandardItemModel(self.form.Catalog)
        self.form.Catalog.setModel(cat_model)

        # First row: "All Catalogs" (mode flag, not checkable)
        all_item = QtGui.QStandardItem("All Catalogs")
        all_item.setData("__ALL__", QtCore.Qt.UserRole)
        all_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        cat_model.appendRow(all_item)

        # Remaining rows: individual catalogs (checkable)
        for catalog_name in self.all_catalog_names:
            it = QtGui.QStandardItem(catalog_name)
            it.setData(catalog_name, QtCore.Qt.UserRole)
            it.setFlags(
                QtCore.Qt.ItemIsEnabled
                | QtCore.Qt.ItemIsSelectable
                | QtCore.Qt.ItemIsUserCheckable
            )
            it.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
            cat_model.appendRow(it)

        # Install a popup event filter to support Ctrl+Click without forcing showPopup()
        self._catalog_popup_filter = _CatalogPopupFilter(self, self.form.Catalog)
        self.form.Catalog.view().viewport().installEventFilter(
            self._catalog_popup_filter
        )

        # Default: first real catalog if present; otherwise "All Catalogs" mode
        if self.all_catalog_names:
            self._set_all_catalogs_mode(False)
            self._set_checked_catalogs([self.all_catalog_names[0]])
            self.form.Catalog.setCurrentIndex(1)
            self._sync_catalog_display_text()
        else:
            self._set_all_catalogs_mode(True)
            self.form.Catalog.setCurrentIndex(0)
            self._sync_catalog_display_text()

        # Dictionary to cache the material availability
        self.__material_available_cache__ = {}

        # Pre-build set of all available materials for fast lookup
        self._all_available_materials = self._build_material_set()

        # Setup search with debouncing (300ms delay)
        self.search_timer = QtCore.QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._doSearch)

        # Connect signals
        self.form.SearchField.textChanged.connect(self._onSearchChanged)
        self.form.AvailableOnlyCheckbox.stateChanged.connect(self._onSearchChanged)
        self.form.Catalog.currentIndexChanged.connect(self.catalogChange)
        self.form.Reference.currentIndexChanged.connect(self.referenceChange)

        # Initialize
        self.catalogChange(self.form.Catalog.currentIndex())

    def _onSearchChanged(self, *args):
        """Debounce search input - wait 300ms after last change"""
        self.search_timer.stop()
        self.search_timer.start(300)

    def _part_matches_search(self, part, catalog_obj, search_words):
        """Check if a part matches all search words (AND logic).

        Searches in part name and all descriptor fields.
        Returns True if ALL words are found somewhere in the part data.
        """
        # Build searchable text from part name and descriptor
        searchable_text = part.lower()
        try:
            descriptor = catalog_obj.descriptor(part)
            for key, value in descriptor.items():
                searchable_text += " " + str(value).lower()
        except (KeyError, AttributeError, TypeError):
            pass

        # Check that ALL words are found
        for word in search_words:
            if word not in searchable_text:
                return False
        return True

    def _doSearch(self):
        """Execute the search/filter"""
        search_text = self.form.SearchField.text().strip().lower()
        show_available_only = self.form.AvailableOnlyCheckbox.isChecked()

        if self._all_catalogs_mode:
            self._doMultiCatalogSearch(
                self.all_catalog_names, search_text, show_available_only
            )
            return

        checked = self._checked_catalogs()
        if len(checked) == 1:
            catalog_name = checked[0]
            self._doSingleCatalogSearch(
                catalog_name,
                self._get_catalog_parts(catalog_name),
                search_text,
                show_available_only,
            )
        elif len(checked) > 1:
            self._doMultiCatalogSearch(checked, search_text, show_available_only)
        else:
            # Fallback: if nothing is checked, behave like "All Catalogs"
            self._doMultiCatalogSearch(
                self.all_catalog_names, search_text, show_available_only
            )

    def _doSingleCatalogSearch(
        self, catalog_name, all_parts, search_text, show_available_only
    ):
        """Search within a single catalog"""
        catalog_obj = self._catalog_cache.get(catalog_name)
        if catalog_obj is None:
            return

        # Split search into words (AND logic - all words must match)
        search_words = search_text.split() if search_text else []

        # Filter by search text (searches part name and all descriptor fields)
        if search_words:
            filtered = []
            for part in all_parts:
                if self._part_matches_search(part, catalog_obj, search_words):
                    filtered.append(part)
        else:
            filtered = list(all_parts)

        # Filter by availability if checkbox is checked
        if show_available_only:
            filtered = [p for p in filtered if self.is_available(catalog_name, p)]

        # Update Reference dropdown
        self.form.Reference.blockSignals(True)
        self.form.Reference.clear()

        if filtered:
            for part in filtered:
                self.form.Reference.addItem(part, catalog_name)
            self.form.Reference.setEnabled(True)
        else:
            self.form.Reference.addItem("No matching parts found")
            self.form.Reference.setEnabled(False)

        self.form.Reference.blockSignals(False)

        # Update info panel for first result
        if filtered and self.form.Reference.isEnabled():
            self.referenceChange(0)

    def _doMultiCatalogSearch(self, catalogs, search_text, show_available_only):
        """Search across multiple catalogs"""
        results = []  # List of (catalog_name, part_name) tuples

        # Split search into words (AND logic - all words must match)
        search_words = search_text.split() if search_text else []

        for catalog_name in catalogs:
            catalog_obj = self._catalog_cache.get(catalog_name)
            if catalog_obj is None:
                continue

            try:
                all_parts = sorted(catalog_obj.parts())

                # Filter by search text (searches part name and all descriptor fields)
                if search_words:
                    filtered = []
                    for part in all_parts:
                        if self._part_matches_search(part, catalog_obj, search_words):
                            filtered.append(part)
                else:
                    filtered = all_parts

                # Filter by availability
                if show_available_only:
                    filtered = [
                        p for p in filtered if self.is_available(catalog_name, p)
                    ]

                # Add to results
                for part in filtered:
                    results.append((catalog_name, part))

            except (AttributeError, KeyError):
                continue

        # Update Reference dropdown with grouped results
        self.form.Reference.blockSignals(True)
        self.form.Reference.clear()

        if results:
            current_catalog = None
            for catalog_name, part_name in results:
                # Add catalog header when catalog changes
                if catalog_name != current_catalog:
                    header = f"── {catalog_name} ──"
                    self.form.Reference.addItem(header, None)
                    # Make header non-selectable
                    idx = self.form.Reference.count() - 1
                    self.form.Reference.model().item(idx).setEnabled(False)
                    current_catalog = catalog_name

                # Add part with catalog info stored in itemData
                self.form.Reference.addItem(f"  {part_name}", catalog_name)

            self.form.Reference.setEnabled(True)

            # Select first valid item (skip header)
            for i in range(self.form.Reference.count()):
                if self.form.Reference.itemData(i) is not None:
                    self.form.Reference.setCurrentIndex(i)
                    break
        else:
            self.form.Reference.addItem("No matching parts found")
            self.form.Reference.setEnabled(False)

        self.form.Reference.blockSignals(False)

        # Update info panel
        if results and self.form.Reference.isEnabled():
            self.referenceChange(self.form.Reference.currentIndex())

    def catalogChange(self, *args):
        """Handle catalog dropdown change"""
        # Clear search field when catalog changes
        self.form.SearchField.clear()

        idx = self.form.Catalog.currentIndex()
        model = self.form.Catalog.model()
        item = model.item(idx) if hasattr(model, "item") else None
        data = item.data(QtCore.Qt.UserRole) if item is not None else None

        if data == "__ALL__":
            self._set_all_catalogs_mode(True)
            self._clear_checked_catalogs()
            self._sync_catalog_display_text()
            self._doMultiCatalogSearch(self.all_catalog_names, "", False)
            return

        # Normal selection of a catalog row switches out of all-mode and acts like single-select
        if isinstance(data, str) and data:
            catalog_name = data
            self._set_all_catalogs_mode(False)
            self._set_checked_catalogs([catalog_name])
            self._sync_catalog_display_text()

            parts = self._get_catalog_parts(catalog_name)
            self.form.Reference.blockSignals(True)
            self.form.Reference.clear()
            for part in parts:
                self.form.Reference.addItem(part, catalog_name)
            self.form.Reference.setEnabled(True)
            self.form.Reference.blockSignals(False)
            if parts:
                self.referenceChange(0)

    def _build_material_set(self):
        """Build a set of all available material names for fast lookup.

        This avoids slow file I/O checks by using the material library's
        metadata methods instead of trying to load each material.
        """
        available = set()
        try:
            # Get all glass library names
            libraries = material.get_glass_libraries()
            for lib in libraries:
                # Get all materials in this library
                materials = material.get_glass_materials_from_library(lib)
                available.update(materials)
        except (AttributeError, Exception):
            # Fallback: return empty set, will use slow method
            pass
        return available

    def _get_catalog_parts(self, catalog_name):
        """Return sorted parts list for a catalog (cached)."""
        if catalog_name in self._catalog_parts_cache:
            return self._catalog_parts_cache[catalog_name]
        catalog_obj = self._catalog_cache.get(catalog_name)
        if catalog_obj is None:
            self._catalog_parts_cache[catalog_name] = []
            return self._catalog_parts_cache[catalog_name]
        try:
            parts = sorted(catalog_obj.parts())
        except Exception:
            parts = []
        self._catalog_parts_cache[catalog_name] = parts
        return parts

    def _set_all_catalogs_mode(self, enabled):
        self._all_catalogs_mode = bool(enabled)

    def _clear_checked_catalogs(self):
        model = self.form.Catalog.model()
        if not hasattr(model, "rowCount") or not hasattr(model, "item"):
            return
        for r in range(model.rowCount()):
            it = model.item(r)
            if it is None:
                continue
            if it.flags() & QtCore.Qt.ItemIsUserCheckable:
                it.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

    def _set_checked_catalogs(self, names):
        wanted = set(names or [])
        model = self.form.Catalog.model()
        if not hasattr(model, "rowCount") or not hasattr(model, "item"):
            return
        for r in range(model.rowCount()):
            it = model.item(r)
            if it is None:
                continue
            if not (it.flags() & QtCore.Qt.ItemIsUserCheckable):
                continue
            cat_name = it.data(QtCore.Qt.UserRole)
            it.setData(
                QtCore.Qt.Checked if cat_name in wanted else QtCore.Qt.Unchecked,
                QtCore.Qt.CheckStateRole,
            )

    def _checked_catalogs(self):
        out = []
        model = self.form.Catalog.model()
        if not hasattr(model, "rowCount") or not hasattr(model, "item"):
            return out
        for r in range(model.rowCount()):
            it = model.item(r)
            if it is None:
                continue
            if not (it.flags() & QtCore.Qt.ItemIsUserCheckable):
                continue
            if it.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
                cat_name = it.data(QtCore.Qt.UserRole)
                if cat_name:
                    out.append(cat_name)
        return out

    def _sync_catalog_display_text(self):
        if self._all_catalogs_mode:
            self.form.Catalog.setEditText("All Catalogs")
            return
        checked = self._checked_catalogs()
        if len(checked) == 1:
            self.form.Catalog.setEditText(checked[0])
        elif len(checked) > 1:
            self.form.Catalog.setEditText("{} catalogs".format(len(checked)))
        else:
            # Should not usually happen; keep something sensible
            self.form.Catalog.setEditText("Catalogs")

    def is_material_available(self, reference):
        # Fast lookup in pre-built set
        return reference in self._all_available_materials

    def _validate_and_get_matcat(self, mat, glass_catalogs):
        """Validate material is in allowed glass catalogs and return its catalog name.

        Args:
            mat: Material name to validate
            glass_catalogs: String of allowed glass catalog names (lowercase)

        Returns:
            The material catalog name

        Raises:
            ValueError: If material's catalog is not in allowed glass_catalogs
        """
        matcat = material.find_material(mat, exact=True, unalias=True)[0][0]
        if matcat not in glass_catalogs:
            raise ValueError(
                f"Trying to use wrong glass catalog: {matcat} not in {glass_catalogs}"
            )
        return matcat

    def is_available(self, catalog, reference):
        # Use cached catalog object
        catalog_obj = self._catalog_cache.get(catalog)
        if catalog_obj is None:
            return False

        part_descriptor = catalog_obj.descriptor(reference)
        ok = True
        comp_type = part_descriptor["type"]
        if comp_type == "SphericalLens":
            comp_mat = part_descriptor["material"]
            if not self.is_material_available(comp_mat):
                print("material {} not found".format(comp_mat))
                ok = False

        elif comp_type == "CylindricalLens":
            comp_mat = part_descriptor["material"]
            if not self.is_material_available(comp_mat):
                print("material {} not found".format(comp_mat))
                ok = False

        elif comp_type in ["Doublet", "AirSpacedDoublet"]:
            comp_mat1 = part_descriptor["material_l1"]
            comp_mat2 = part_descriptor["material_l2"]

            if not self.is_material_available(comp_mat1):
                print("material {} not found".format(comp_mat1))
                ok = False

            if not self.is_material_available(comp_mat2):
                print("material {} not found".format(comp_mat2))
                ok = False
        else:
            print("Component Type {} not found".format(comp_type))
            ok = False

        return ok

    def _get_unavailable_reason(self, catalog, reference, part_descriptor):
        """Determine why a component is unavailable.

        Returns a user-friendly reason string explaining which material is missing.
        """
        comp_type = part_descriptor.get("type", "Unknown")

        # Check material fields based on component type
        if comp_type in ["SphericalLens", "CylindricalLens", "AsphericLens"]:
            comp_mat = part_descriptor.get("material", "Unknown")
            if not self.is_material_available(comp_mat):
                return f"material {comp_mat} not found"

        elif comp_type in ["Doublet", "AirSpacedDoublet"]:
            comp_mat1 = part_descriptor.get("material_l1", "Unknown")
            comp_mat2 = part_descriptor.get("material_l2", "Unknown")

            if not self.is_material_available(comp_mat1):
                return f"material {comp_mat1} not found"
            if not self.is_material_available(comp_mat2):
                return f"material {comp_mat2} not found"

        # Generic fallback for unknown types
        for key, value in part_descriptor.items():
            if "material" in key.lower() and isinstance(value, str):
                if not self.is_material_available(value):
                    return f"material {value} not found"

        return "unknown reason"

    def referenceChange(self, *args):
        # Skip if dropdown is disabled (no valid selection)
        if not self.form.Reference.isEnabled():
            self.form.Info.clear()
            self.form.Status.setText("")
            return

        # Get catalog from Reference itemData (handles multi-catalog mode)
        catalog = self.form.Reference.currentData()
        reference = self.form.Reference.currentText().strip()

        # Skip if no valid catalog or reference
        if catalog is None or not reference:
            self.form.Info.clear()
            self.form.Status.setText("")
            return

        try:
            part_descriptor = getattr(library, catalog).descriptor(reference)

            # Check availability
            try:
                is_available = self.is_available(catalog, reference)
            except KeyError:
                is_available = False

            # Get unavailable reason if needed
            unavailable_reason = None
            if not is_available:
                unavailable_reason = self._get_unavailable_reason(
                    catalog, reference, part_descriptor
                )

            # Format component info using new generic formatter
            try:
                formatter = ComponentInfoFormatter()
                formatted_info = formatter.format_component_info(
                    catalog,
                    reference,
                    part_descriptor,
                    is_available=is_available,
                    unavailable_reason=unavailable_reason,
                )
                self.form.Info.setPlainText(formatted_info)
            except Exception as e:
                # Fallback to original plain text display on any formatting error
                FreeCAD.Console.PrintWarning(f"Info formatting failed: {e}\n")
                self.form.Info.clear()
                for option in part_descriptor:
                    self.form.Info.insertPlainText(
                        "{} = {}\n".format(option, part_descriptor[option])
                    )

            # Update status indicator (keep existing separate status label for now)
            if is_available:
                self.form.Status.setText("Component Available")
                self.form.Status.setStyleSheet("color: green")
            else:
                self.form.Status.setText("Component not Available")
                self.form.Status.setStyleSheet("color: red")
        except (KeyError, AttributeError):
            # Invalid reference
            self.form.Info.clear()
            self.form.Status.setText("")

    @FeedbackHelper.with_error_handling("Catalog Component")
    def accept(self):
        # Get catalog from Reference itemData (handles multi-catalog mode)
        catalog = self.form.Reference.currentData()
        reference = self.form.Reference.currentText().strip()

        # Validate we have a valid selection
        if catalog is None:
            raise ValueError("No valid component selected")

        if self.is_available(catalog, reference):
            part_descriptor = getattr(library, catalog).descriptor(reference)
            comptype = part_descriptor["type"]
            glass_catalogs = part_descriptor["glass_catalogs"].lower()

            X = self.form.Xpos.value()
            Y = self.form.Ypos.value()
            Z = self.form.Zpos.value()
            Xrot = self.form.Xrot.value()
            Yrot = self.form.Yrot.value()
            Zrot = self.form.Zrot.value()

            obj = None

            if comptype == "SphericalLens":
                mat = part_descriptor["material"]
                th = part_descriptor["thickness"]
                diam = 2.0 * part_descriptor["radius"]
                c1 = part_descriptor["curvature_s1"]
                c2 = part_descriptor["curvature_s2"]
                matcat = self._validate_and_get_matcat(mat, glass_catalogs)
                obj = InsertSL(c1, c2, th, diam, "L", matcat, mat)

            elif comptype == "CylindricalLens":
                mat = part_descriptor["material"]
                th = part_descriptor["thickness"]
                size = part_descriptor["size"]
                c1 = part_descriptor["curvature_s1"]
                c2 = part_descriptor["curvature_s2"]
                matcat = self._validate_and_get_matcat(mat, glass_catalogs)
                obj = InsertCL(c1, c2, th, 2 * size[1], 2 * size[0], "L", matcat, mat)

            elif comptype == "Doublet":
                mat1 = part_descriptor["material_l1"]
                mat2 = part_descriptor["material_l2"]
                th1 = part_descriptor["thickness_l1"]
                th2 = part_descriptor["thickness_l2"]
                diam = 2.0 * part_descriptor["radius"]
                c1 = part_descriptor["curvature_s1"]
                c2 = part_descriptor["curvature_s2"]
                c3 = part_descriptor["curvature_s3"]
                matcat1 = self._validate_and_get_matcat(mat1, glass_catalogs)
                matcat2 = self._validate_and_get_matcat(mat2, glass_catalogs)

                obj = InsertDL(
                    c1,
                    c2,
                    th1,
                    c2,
                    c3,
                    th2,
                    diam,
                    0,
                    "L",
                    matcat1,
                    mat1,
                    matcat2,
                    mat2,
                )

            elif comptype == "AirSpacedDoublet":
                mat1 = part_descriptor["material_l1"]
                mat2 = part_descriptor["material_l2"]
                th1 = part_descriptor["thickness_l1"]
                th2 = part_descriptor["thickness_l2"]
                airgap = part_descriptor["air_gap"]
                diam = 2.0 * part_descriptor["radius"]
                c1 = part_descriptor["curvature_s1"]
                c2 = part_descriptor["curvature_s2"]
                c3 = part_descriptor["curvature_s3"]
                c4 = part_descriptor["curvature_s4"]
                matcat1 = self._validate_and_get_matcat(mat1, glass_catalogs)
                matcat2 = self._validate_and_get_matcat(mat2, glass_catalogs)

                obj = InsertDL(
                    c1,
                    c2,
                    th1,
                    c3,
                    c4,
                    th2,
                    diam,
                    airgap,
                    "L",
                    matcat1,
                    mat1,
                    matcat2,
                    mat2,
                )

            else:
                raise ValueError(f"Unknown component type: {comptype}")

            if obj is not None:
                m = FreeCAD.Matrix()
                m.rotateX(radians(Xrot))
                m.rotateY(radians(Yrot))
                m.rotateZ(radians(Zrot))
                m.move((X, Y, Z))
                p1 = FreeCAD.Placement(m)
                obj.Placement = p1
                obj.Reference = "{} - {}".format(catalog, reference)
            # Note: closeDialog(), recompute(), and updateGui() handled by decorator


class CatalogComponentMenu(WBCommandMenu):
    def __init__(self):
        WBCommandMenu.__init__(self, CatalogComponentGUI)

    def GetResources(self):
        from freecad.pyoptools import ICONPATH
        import os

        # Base tooltip
        tooltip = "Search and insert components from catalog (Ctrl+Shift+F)"

        # Add disabled reason if not active
        if not self.IsActive():
            tooltip += " - Disabled: No document open"

        return {
            "MenuText": "Catalog Component",
            "Accel": "Ctrl+Shift+F",
            "ToolTip": tooltip,
            "Pixmap": os.path.join(ICONPATH, "search-components.svg"),
        }


class _CatalogPopupFilter(QtCore.QObject):
    """Support Ctrl+Click multi-select in a QComboBox without forcing showPopup().

    - Ctrl+Click on a catalog row toggles its check state and keeps popup open.
    - Normal click behaves like a regular combobox selection.
    - "All Catalogs" is a mode flag, not a checkable selection.
    """

    def __init__(self, gui, combo):
        super(_CatalogPopupFilter, self).__init__(combo)
        self._gui = gui
        self._combo = combo
        self._pending_toggle_row = None

    def _should_toggle(self, item, idx, pos):
        """Return True if this click should toggle checkstate.

        Toggle when Ctrl is held, or when the click is on the checkbox indicator.
        """
        if not (item.flags() & QtCore.Qt.ItemIsUserCheckable):
            return False

        mods = QtWidgets.QApplication.keyboardModifiers()
        if bool(mods & QtCore.Qt.ControlModifier):
            return True

        # Allow direct checkbox clicks without Ctrl.
        view = self._combo.view()
        opt = QtWidgets.QStyleOptionViewItem()
        opt.initFrom(view)
        opt.rect = view.visualRect(idx)
        opt.state |= QtWidgets.QStyle.State_HasFocus
        check_rect = view.style().subElementRect(
            QtWidgets.QStyle.SE_ItemViewItemCheckIndicator, opt, view
        )
        return check_rect.contains(pos)

    def eventFilter(self, obj, event):
        et = event.type()
        if et not in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease):
            return False

        view = self._combo.view()
        idx = view.indexAt(event.pos())
        if not idx.isValid():
            self._pending_toggle_row = None
            return False

        model = self._combo.model()
        item = model.itemFromIndex(idx) if hasattr(model, "itemFromIndex") else None
        if item is None:
            self._pending_toggle_row = None
            return False

        data = item.data(QtCore.Qt.UserRole)
        if data == "__ALL__":
            self._pending_toggle_row = None
            return False

        # On press: decide whether we will handle this click as a toggle.
        if et == QtCore.QEvent.MouseButtonPress:
            if self._should_toggle(item, idx, event.pos()):
                self._pending_toggle_row = idx.row()
                return True  # swallow so combobox doesn't change currentIndex/close
            self._pending_toggle_row = None
            return False

        # On release: if we swallowed the press, perform the toggle here.
        if self._pending_toggle_row != idx.row():
            return False
        self._pending_toggle_row = None

        if not (item.flags() & QtCore.Qt.ItemIsUserCheckable):
            return True

        new_state = (
            QtCore.Qt.Unchecked
            if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked
            else QtCore.Qt.Checked
        )
        # Block signals defensively in case some styles still adjust currentIndex.
        self._combo.blockSignals(True)
        item.setData(new_state, QtCore.Qt.CheckStateRole)
        self._combo.blockSignals(False)

        # Toggle switches out of all-catalogs mode
        self._gui._set_all_catalogs_mode(False)

        # Ensure at least one catalog remains checked
        checked = self._gui._checked_catalogs()
        if not checked:
            item.setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
            checked = [data]

        self._gui._sync_catalog_display_text()
        self._gui._doMultiCatalogSearch(
            checked,
            self._gui.form.SearchField.text().strip().lower(),
            self._gui.form.AvailableOnlyCheckbox.isChecked(),
        )
        return True
