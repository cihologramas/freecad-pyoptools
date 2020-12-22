Creating a new optical model
============================

After the workbench is activated, two new menus will appear in FreeCAD menubar,
the `Add Components` menu, and the `Simulate Menu`.


Add Components
--------------

The add components menu has a set of submenus that allow to add optical several
types of optical components to the 3D space where the simulation by raytracing
will be performed. All the windows from the `Add Component` have 2 options in
common that allow to position the component in the 3D space:

Position :
    This option allows the component to be placed at any place in the 3D
    space. The coordinates are given in millimeters, and correspond to the
    point where the component's origin will be placed. The location of the
    component's origin is dependant on the component definition, and must be
    checked in the pyoptools library.

Orientation:
   This option allows the component to be rotated so it faces in the correct
   direction.

   .. Todo::
      Check the rotation definition and write a correct description

After the component is placed, it can be moved and rotated by changing its
`Placement` property. It can also be moved by right clicking on the component
name in the Panel, and selecting `Transform`, like any FreeCAD object.


Catalog Components
^^^^^^^^^^^^^^^^^^

This menu will open a window in the task area of FreeCAD, where some components
from a couple optical catalogs defined in pyOpTools
(`Edmund Optics <https://www.edmundoptics.com/>`_ and
`ThorLabs <https://www.thorlabs.com/>`_ for the moment), can be imported into
the FreeCAD 3D space. This window will allow you to select the component by its
reference, and also to adjust its position, and the orientation.

.. warning::

   This libraries have been created from the data given by the corresponding
   manufacturers to simplify the design and simulation of optical systems,
   however, there is no warranty about its accuracy, nor in terms of its
   mechanical dimensions, or in terms of the accuracy of the simulations.

Lenses
^^^^^^

Sometimes it is needed to simulate lenses that do not exist in any of the
catalogs included with the pyOpTools library. When this is the case, it is
possible to use one of the generic lenses that can be created using the options
given by the `Lenses` menu:

 
Spherical Lens
~~~~~~~~~~~~~~

Creates a round shaped spherical.

Diameter (mm):
    Diameter of the lens.

Center Thickness:
    Thickness of the lens measured at its optical axis.

Curv S1:
    Curvature of the first surface (left hand side in normal optical diagrams)
    of the lens. Positive value will create a convex surface, negative will
    create for concave.

Curv S2:
    Curvature of the second surface (right hand side in normal optical
    diagrams) of the lens. Positive value will create a concave surface,
    negative will create for convex.

Material:
   Select the material used to buoild the lens from diferent material catalogs.
   Also if `Value` catalog is selected, a constant refraction index can be used.

Cylindrical Lens
~~~~~~~~~~~~~~~~
Creates a rectancular shaped cylindrical lens.

Height:
    Height of the lens

Width:
    Width of the lens.

Center Thickness:
    Thickness of the lens measured at its optical axis.

Curv S1:
    Curvature of the first surface (left hand side in normal optical diagrams)
    of the lens. Positive value will create a convex surface, negative will
    create for concave.

Curv S2:
    Curvature of the second surface (right hand side in normal optical
    diagrams) of the lens. Positive value will create a concave surface,
    negative will create for convex.

Material:
   Material used to build the lens. It can be selected from several material
   catalogs. If `Value` catalog is selected, a constant refraction index can
   be used.


Doublet Lens
~~~~~~~~~~~~

Creates a round shaped doublet.

Diameter:
    Diameter of the doublet. It assumes both lenses have the same diameter.

Inter Lens Distance:
    Distance between the lenses measured at the optical axis. If set to 0, the
    2 lenses that compose the doublet are in contact.

Center Thickness (lens 1):
    Thickness of the lens 1 measured at its optical axis.

Curv S1 (lens 1):
    Curvature of the first surface (left hand side in normal optical diagrams)
    of the lens 1. Positive value will create a convex surface, negative will
    create for concave.

Curv S2 (lens 1):
    Curvature of the second surface (right hand side in normal optical
    diagrams) of the lens 1. Positive value will create a concave surface,
    negative will create for convex.

Material (lens 1):
   Material used to build the lens 1. It can be selected from several material
   catalogs. If `Value` catalog is selected, a constant refraction index can
   be used.

Center Thickness (lens 2):
    Thickness of the lens 2 measured at its optical axis.

Curv S1 (lens 2):
    Curvature of the first surface (left hand side in normal optical diagrams)
    of the lens 2. Positive value will create a convex surface, negative will
    create for concave. If `Inter Lens Distance = 0` it will take the same
    value as `Curv S2` from lens 1.

Curv S2 (lens 2):
    Curvature of the second surface (right hand side in normal optical
    diagrams) of the lens 2. Positive value will create a concave surface,
    negative will create for convex.

Material (lens 2):
   Material used to build the lens 1. It can be selected from several material
   catalogs. If `Value` catalog is selected, a constant refraction index can
   be used.

Thick Lens
~~~~~~~~~~

Model used to simulate an ideal thick lens. Graphically the thick lens is
represented as a cylinder to give an idea of the lens enclosure size the 2 ends
of the cylinder will be called `surface 1` and `surface 2`, aditionally the
model will have some planes that represent the `Principal Planes` position, and
the pupil position and size.


Diameter:
    Diameter of the lens enclosure.

Lens thickness:
    Thickness of the lens enclosure. Distance from `surface 1` to `surface 2`.

Position Principal Plane 1:
    Position of the principal plane referenced to the cylinder's `surface 1`.
    If 0, the principal plane will be on top of the `surface 1`

Position Principal Plane 2:
    Position of the principal plane referenced to the cylinder's `surface 2`.
    If 0, the principal plane will be on top of the `surface 2`

Focal Lenght:
    Thick lens effective focal length.

Pupil reference surface:
    The pupil can be referenced  to any or the surfaces 1 or 2, and it will
    only act on the rays crossing that surface. If none is selected, the model
    will not have pupil.

Pupil position:
    Distance between the pupil and its reference surface.

Pupil diameter:
    Diameter of the pupil apperture.

Show pupils and principal planes:
   If selected, the pupils and principal planes wuill be shown in the model.

Show full raytrace:
   If selected, the rays will be drawn from the source, into the first
   intersected principal plane, then to the second principal plane, and then
   out from the second principal plane. Depending on the location of the
   principal planes, it is possible the rays seem to travel backward. Also have
   in mind that the principal planes can be auside the enclosure, so the rays
   migth seem do be difracted by an outside element.

   If not selected, the rays wil be drawn into the first enclosure surface, to
   the second enclosure surface, and out from it.

Powel Lens
~~~~~~~~~~

.. todo::
   Document this

Mirrors
^^^^^^^
The mirror option can be used to create flat mirrors and beamsplitters.


Round Mirror
~~~~~~~~~~~~

Rectangular Mirror
~~~~~~~~~~~~~~~~~~

Prisms
^^^^^^

Penta Prism
~~~~~~~~~~~


Dove Prism
~~~~~~~~~~


Beam Splitters
^^^^^^^^^^^^^^

Beam splitting cube
~~~~~~~~~~~~~~~~~~~

Ray Sources
^^^^^^^^^^^

Parallel Ray Source
~~~~~~~~~~~~~~~~~~~

Point Source
~~~~~~~~~~~~

Array of Sources
~~~~~~~~~~~~~~~~

Aperture
^^^^^^^^^


Difraction Gratting
^^^^^^^^^^^^^^^^^^^

Sensor
^^^^^^
