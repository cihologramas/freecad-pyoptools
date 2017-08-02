# -*- coding: utf-8 -*-
import FreeCAD, FreeCADGui


import pyOpToolsWB #Importar los commandos y registrarlos




class pyOpToolsWorkbench ( Workbench ):
    "pyOpTools object"
    Icon = """
 			/* XPM */
 			static const char *test_icon[]={
 			"16 16 2 1",
 			"a c #000000",
 			". c None",
 			"................",
 			"........#.......",
 			".......###......",
 			".....#######....",
 			"...##..###..##..",
 			".......###......",
 			".......###......",
 			".......###......",
 			".......###......",
 			".......###......",
 			".......###......",
 			"...##..###..##..",
 			".....#######....",
 			".......###......",
 			"........#.......",
 			"................",
 			"................"};
 			"""
    MenuText = "pyOpTools"
    ToolTip = "pyOpTools workbench"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):

        self.appendMenu("Add Components", ["SphericalLens","DoubletLens","ThickLens",
                                           "RoundMirror", "RectangularMirror",
                                           "CatalogComponent","Sensor","RaysParallel",
                                           "RaysPoint","RaysArray"])
        self.appendMenu("Simulate", ["Propagate", "Reports","Optimize"])

        Log ("Loading MyModule... done\n")

    def Activated(self):

        # do something here if needed...
        Msg ("MyWorkbench.Activated()\n")
        print FreeCAD.ActiveDocument
    def Deactivated(self):
        # do something here if needed...
        Msg ("MyWorkbench.Deactivated()\n")








FreeCADGui.addWorkbench(pyOpToolsWorkbench)