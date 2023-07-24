# freecad-pyoptools

Workbench to integrate pyoptools with freecad, that means basically optics ray tracing capabilities for FreeCAD.

## Prerequisite

It requires a working [FreeCAD](https://freecadweb.org/) with python3 support,  and [pyoptools](https://github.com/cihologramas/pyoptools) 
installation for python3.

## Linux Installation

Clone directly the git repository into the Mod dir of FreeCAD. This usually
means cloning the repo into ~/.local/share/FreeCAD/Mod directory.

After that you just select the "pyOpTools" workbench in FreeCAD in the usual way. As seen in the following screenshot
![image](https://raw.githubusercontent.com/cihologramas/freecad-pyoptools/master/media/PyOpTools-workbench-selection.png)


## Small Instructions

Please have in mind that this is a work in progress, so it may change radically some day, and your simulations may not run anymore.

The idea behind this workbench is to be able to simulate (by raytracing) optical systems. To do so, you need to build the optical system you want to simulate.

To build the system first change to the pyOpTools workbench. You will find 2 new menus:

* Add Component
* Simulate

The first menu allows you to add optical components to your system. Each component creates a dialog
that can be used to position it, and also to adjust it's parameters such as focal length (for example). There are also some kind of ray sources that must be added to perform a simulation (point source, parallel source). After all the components and ray sources are located in the system, press simulate-> propagate, and the ray tracing simulation will be ran.








