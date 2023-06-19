Installing instructions
=======================

The FreeCad-pyOpTools workbench is being developed under Linux
(`Debian <http://debian.org>`_) and although it should work under Windows, it
has not been tested under such OS.

Requirements
------------

It requires a working `FreeCAD <http://freecadweb.org>`_ installation with
`Python 3 <http://www.python.org>`_ support, and `pyOpTools
<https://github.com/cihologramas/pyoptools>`_.

Linux Installation
------------------

Clone directly the git repository into the Mod dir of FreeCAD. This usually
means cloning the repo into ~/.local/share/FreeCAD/Mod directory::

  cd ~/.local/share/FreeCAD/Mod
  git clone https://github.com/cihologramas/freecad-pyoptools

If Mod folder does not exists, you can create it.

After this, a `pyoptools workbench` should appear in the workbench list of your
FreeCAD installation.
