Installation Guide
==================

The FreeCAD-pyOpTools workbench extends FreeCAD with powerful optical raytracing
capabilities by integrating the pyOpTools library. It facilitates the design 
and simulation of optical systems.


Using the Addon Manager
-----------------------

The Addon Manager in FreeCAD offers the simplest way to install the 
FreeCAD-pyOpTools workbench, managing both the workbench and its dependencies
automatically.

1. Open FreeCAD and navigate to **Tools** -> **Addon Manager**.
2. Locate **FreeCAD-pyOpTools** in the list of available workbenches and select it.
3. Click **Install** and follow the on-screen prompts to complete the installation process.

.. note::

   This installation method has been tested and confirmed to work in the following environments:

   * Windows systems using the official FreeCAD installer.
   * Debian 12 using a self compiled version of FreeCAD 0.21.2.

.. warning::

   During the installation, you will be prompted to install the `pyoptools` module. 
   It is crucial to **select Yes** to this prompt to ensure that the 
   FreeCAD-pyOpTools workbench operates correctly.

Running FreeCAD-pyOpTools with the Official FreeCAD AppImage
------------------------------------------------------------

The FreeCAD-pyOpTools workbench is compatible with the FreeCAD official AppImage
distribution. However, to successfully install and run this workbench using the
FreeCAD AppImage, a specific setup involving a **custom FreeCAD user home folder** 
is required. This approach ensures that the workbench and its dependencies are 
correctly managed within the AppImage environment.

Setting Up a Custom FreeCAD User Home Folder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using the FreeCAD AppImage, it's possible to specify a custom location for
the FreeCAD user home folder. This customization is particularly useful for 
isolating workbench installations or managing different configurations. To run 
the FreeCAD AppImage with a custom user home folder for the FreeCAD-pyOpTools
workbench, follow these steps:

1. Decide on a directory to use as your custom FreeCAD user home. This guide
   uses `~/TEMPFC/` as an example, but you can choose any location that suits
   your needs.

2. Open a terminal window and run the following command, replacing `~/TEMPFC/` 
   with your chosen directory if different, and adjusting the AppImage filename
   as necessary for your version of FreeCAD:

   .. code-block:: bash

      $ FREECAD_USER_HOME=~/TEMPFC/ FreeCAD-0.21.2-Linux-x86_64.AppImage

   This command sets the `FREECAD_USER_HOME` environment variable to your custom
   directory (`~/TEMPFC/` in this example) for the duration of the FreeCAD 
   session. The FreeCAD AppImage will use this location as the user home 
   folder, storing configurations and workbench installations there.

3. With FreeCAD running, proceed to install the FreeCAD-pyOpTools workbench 
   using the Addon Manager as described in the `[Installation Guide](installation.rst)`.

.. note::

   Each time you wish to use the FreeCAD-pyOpTools workbench or access the 
   configurations stored in the custom user home folder, you will need to launch
   the FreeCAD AppImage with the `FREECAD_USER_HOME` environment variable set
   as shown above.

By following these instructions, you can use the FreeCAD-pyOpTools workbench 
with the official FreeCAD AppImage, ensuring that all necessary files and 
configurations are correctly handled.
