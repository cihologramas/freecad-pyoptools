# Visual Feedback Implementation Guide for Developers

This guide explains how to add visual feedback to pyOpTools components following the pattern established in Story 1.6.

## Overview

All visual feedback is handled through the `FeedbackHelper` class in `feedback.py`. Error handling is implemented using Python decorators for clean, maintainable code.

## Adding Error Handling to Components

### For Component Creation Dialogs

Add the `@FeedbackHelper.with_error_handling()` decorator to your `accept()` method:

```python
from .feedback import FeedbackHelper

class MyComponentGUI(WBCommandGUI):
    @FeedbackHelper.with_error_handling("My Component")
    def accept(self):
        # Your component creation logic here
        obj = InsertMyComponent(...)
        obj.Placement = placement
        
        # That's it! Decorator automatically handles:
        # - FreeCAD.ActiveDocument.recompute()
        # - FreeCADGui.updateGui()
        # - FreeCADGui.Control.closeDialog()
```

**That's it!** The decorator automatically:
- Catches all exceptions
- Logs technical details for debugging
- Shows user-friendly error dialog with recovery actions
- Never shows stack traces to users
- **Calls recompute(), updateGui(), and closeDialog() for you**

### For Operations (Optimize, etc.)

For operations that modify existing components, use `operation="execution"`:

```python
from .feedback import FeedbackHelper

class OptimizeGUI(WBCommandGUI):
    @FeedbackHelper.with_error_handling("Optimization", operation="execution")
    def accept(self):
        # Perform your operation
        result = perform_optimization(...)
        show_results(result)
        
        # Decorator automatically handles:
        # - FreeCADGui.updateGui()
        # - FreeCADGui.Control.closeDialog()
        # Note: Does NOT call recompute() since nothing new was created
```

### For Other Operations (Propagate, etc.)

For operations in `Activated()` methods, wrap in try-except:

```python
from .feedback import FeedbackHelper

def Activated(self):
    try:
        # Operation logic
        result = perform_operation()
        
        # Success feedback
        FeedbackHelper.show_success(f"Operation complete - {result}")
        
    except Exception as e:
        FeedbackHelper.show_error_dialog(
            "Operation Failed",
            FeedbackHelper.format_error(
                e,
                "Could not complete operation.\n\n"
                "Please ensure:\n"
                "• Prerequisites are met\n"
                "• Parameters are valid"
            )
        )
```

### For Long Operations (>200ms)

Use the `@FeedbackHelper.with_busy_cursor` decorator:

```python
from .feedback import FeedbackHelper

class MyPart(WBPart):
    @FeedbackHelper.with_busy_cursor
    def execute(self, obj):
        # Long computation here
        perform_ray_trace()
```

## Components Needing Updates

The following component files need the `@FeedbackHelper.with_error_handling()` decorator added to their `accept()` method:

**Lenses:**
- [ ] `cylindricallens.py` - `@FeedbackHelper.with_error_handling("Cylindrical Lens")`
- [ ] `doubletlens.py` - `@FeedbackHelper.with_error_handling("Doublet Lens")`
- [ ] `thicklens.py` - `@FeedbackHelper.with_error_handling("Thick Lens")`
- [ ] `powelllens.py` - `@FeedbackHelper.with_error_handling("Powell Lens")`
- [ ] `lensdata.py` - `@FeedbackHelper.with_error_handling("Lens from Catalog")`

**Mirrors:**
- [ ] `roundmirror.py` - `@FeedbackHelper.with_error_handling("Round Mirror")`
- [ ] `rectmirror.py` - `@FeedbackHelper.with_error_handling("Rectangular Mirror")`

**Prisms:**
- [ ] `pentaprism.py` - `@FeedbackHelper.with_error_handling("Penta Prism")`
- [ ] `doveprism.py` - `@FeedbackHelper.with_error_handling("Dove Prism")`
- [ ] `rightangleprism.py` - `@FeedbackHelper.with_error_handling("Right Angle Prism")`
- [ ] `bscube.py` - `@FeedbackHelper.with_error_handling("Beam Splitter Cube")`

**Optical Elements:**
- [ ] `diffractiongratting.py` - `@FeedbackHelper.with_error_handling("Diffraction Grating")`
- [ ] `aperture.py` - `@FeedbackHelper.with_error_handling("Aperture")`

**Sensors:**
- [ ] `sensor.py` - `@FeedbackHelper.with_error_handling("Sensor")`

**Ray Sources:**
- [ ] `ray.py` - `@FeedbackHelper.with_error_handling("Ray")`
- [ ] `rayspoint.py` - `@FeedbackHelper.with_error_handling("Point Source")`
- [ ] `raysparallel.py` - `@FeedbackHelper.with_error_handling("Parallel Rays")`
- [ ] `raysarray.py` - `@FeedbackHelper.with_error_handling("Ray Array")`

**Special:**
- [ ] `catalogcomponent.py` - Already has error handling, may need decorator refactor

## Completed Components

- [x] `sphericallens.py` - Reference implementation
- [x] `propagate.py` - Operations with feedback

## Testing

After adding decorators, test each component:

1. **Happy Path**: Create component with valid parameters - should work silently
2. **Invalid Parameters**: Try negative values, zero dimensions - should show user-friendly error
3. **No Document**: Try creating without open document - should explain to create document
4. **Dialog Opening**: Test that dialog opens successfully

## Success Criteria

- ✅ No manual try-except blocks in component accept() methods (decorator handles it)
- ✅ Error messages are user-friendly (no stack traces)
- ✅ Technical errors logged to console for debugging
- ✅ Consistent error message format across all components
