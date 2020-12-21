Creating a new optical model
============================

After the workbench is activated, two new menus will appear in FreeCAD menubar,
the `Add Components` menu, and the `Simulate Menu`.


Add Components
--------------

The add components menu has a set of submenus that allow to add optical several
types of optical components to the 3D space where the simulation by raytracing
will be performed. 


Catalog Components
^^^^^^^^^^^^^^^^^^

This menu will open a window in the task area of FreeCAD, where some components
from a couple optical catalogs defined in pyOpTools
(`Edmund Optics <https://www.edmundoptics.com/>`_ and
`ThorLabs <https://www.thorlabs.com/>`_ for the moment), can be imported into
the FreeCAD 3D space. This window will allow you to select the component by its
reference, and also to adjust its position, and the orientation.
After the component is placed on the 3D space, it can be moved and rotated to
fix its position and orientation by using the normal FreeCAD tools for this
purpose.

.. warning::

   This libraries have been created from the data given by the corresponding
   manufacturers to simplify the design and simulation of optical systems,
   however, there is no warranty about its accuracy, nor in terms of its
   mechanical dimensions, or in terms of the accuracy of the simulations.

Lenses
^^^^^^

Sometimes we need to simulate lenses that do not exist in any of the catalogs
included with the pyOpTools library. When this is the case, the `Lenses` menu
contain a set of submenus for this purpose:

Spherical Lens
~~~~~~~~~~~~~~




Cylindrical Lens
~~~~~~~~~~~~~~~~


Doublet Lens
~~~~~~~~~~~~


Thick Lens
~~~~~~~~~~


Powel Lens
~~~~~~~~~~



Mirrors
^^^^^^^


Prisms
^^^^^^

Beam Splitters
^^^^^^^^^^^^^^


Ray Sources
^^^^^^^^^^^


Apperture
^^^^^^^^^


Difraction Gratting
^^^^^^^^^^^^^^^^^^^

Sensor
^^^^^^
