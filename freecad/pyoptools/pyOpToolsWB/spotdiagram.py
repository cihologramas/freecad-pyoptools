# -*- coding: utf-8 -*-
import os
import FreeCAD
import traceback
from freecad.pyoptools import ICONPATH
from .feedback import FeedbackHelper

try:
    # FreeCAD 0.20+ (core module)
    from FreeCAD.Plot import Plot
except ImportError:
    try:
        # FreeCAD 0.19 (external add-on)
        from freecad.plot import Plot
    except ImportError:
        Plot = None

from .propagate import PropagatePart

class SpotDiagramMenu:
    def __init__(self):
        #Esta no tiene GUI, no necesitamos heredar de WBCommandMenu
        #WBCommandMenu.__init__(self,None)
        pass

    def GetResources(self):
        # Base tooltip
        tooltip = "Generate spot diagrams from sensor ray hit data"
        
        # Add disabled reason if not active
        if not self.IsActive():
            if FreeCAD.ActiveDocument is None:
                tooltip += " - Disabled: No document open"
            elif Plot is None:
                tooltip += " - Disabled: Plot module not available"
        
        return {"MenuText": "Spot Diagram",
                #"Accel": "Ctrl+M",
                "ToolTip": tooltip,
                "Pixmap": os.path.join(ICONPATH, "spot-diagram.svg")}

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        if Plot is None:
            return False
        return True

    @FeedbackHelper.with_busy_cursor
    def Activated(self):
        if Plot is None:
            FeedbackHelper.show_error_dialog(
                "Plot Module Not Available",
                "The FreeCAD Plot module is not available.\n\n"
                "For FreeCAD 0.19: Install the Plot Workbench via Add-on Manager\n"
                "For FreeCAD 0.20+: Plot module should be included by default\n\n"
                "Please install the Plot module and try again."
            )
            return
        
        try:
            objs = FreeCAD.ActiveDocument.Objects
            FreeCAD.Console.PrintMessage(f"Total objects in document: {len(objs)}\n")

            # Filter optical objects
            opobjs = list(filter(lambda x: hasattr(x, "ComponentType"), objs))
            FreeCAD.Console.PrintMessage(f"Optical objects found: {len(opobjs)}\n")

            # Find all sensors
            a_sensors = list(filter(lambda x: x.ComponentType == "Sensor", opobjs))
            FreeCAD.Console.PrintMessage(f"All sensors: {len(a_sensors)}\n")

            # Filter enabled sensors
            sensors = list(filter(lambda x: x.Enabled, a_sensors))
            FreeCAD.Console.PrintMessage(f"Enabled sensors: {len(sensors)}\n")

            if not sensors:
                FeedbackHelper.show_error_dialog(
                    "No Active Sensors",
                    "No enabled sensors found in the document.\n\n"
                    "Please add and enable at least one sensor before generating reports."
                )
                return

            # Get sensor labels
            slabels = list(map(lambda x: x.Label, sensors))
            FreeCAD.Console.PrintMessage(f"Sensor labels: {slabels}\n")

            # Find propagations
            props = list(filter(lambda x: x.ComponentType == "Propagation", opobjs))
            FreeCAD.Console.PrintMessage(f"Propagations found: {len(props)}\n")

            if not props:
                FeedbackHelper.show_error_dialog(
                    "No Propagation Results",
                    "No ray propagation results found.\n\n"
                    "Please run ray propagation (Propagate command) before generating reports."
                )
                return

            # Get optical systems from propagations
            ss = list(map(lambda x: x.Proxy.S, props))
            FreeCAD.Console.PrintMessage(f"Optical systems to process: {len(ss)}\n")
            
            plot_count = 0
            for idx_s, s in enumerate(ss):
                FreeCAD.Console.PrintMessage(f"\nProcessing optical system {idx_s + 1}/{len(ss)}\n")
                for n in slabels:
                    FreeCAD.Console.PrintMessage(f"  Checking sensor: {n}\n")
                    try:
                        ccd = s[n][0]
                        FreeCAD.Console.PrintMessage(f"    Found CCD data for {n}\n")
                        hl = ccd.hit_list
                        FreeCAD.Console.PrintMessage(f"    Hit list length: {len(hl)}\n")
                        
                        if len(hl) == 0:
                            FreeCAD.Console.PrintWarning(
                                f"Sensor '{n}' has no ray hits. Skipping plot.\n"
                            )
                            continue
                        
                        # Extract hit positions
                        FreeCAD.Console.PrintMessage(f"    Extracting hit positions...\n")
                        X = []
                        Y = []
                        for i in hl:
                            p = i[0]
                            # Hitlist[1] points to the incident ray
                            # col = wavelength2RGB(i[1].wavelength)
                            X.append(p[0])
                            Y.append(p[1])
                        
                        FreeCAD.Console.PrintMessage(f"    Extracted {len(X)} data points\n")
                        
                        # Create a new plot document for this sensor's spot diagram
                        # This creates a separate tab/window for each plot
                        FreeCAD.Console.PrintMessage(f"    Creating plot figure...\n")
                        Plot.figure(f"SpotDiagram_{n}")
                        
                        # Get axes to configure plot appearance
                        FreeCAD.Console.PrintMessage(f"    Configuring plot axes...\n")
                        ax = Plot.axes()
                        if ax:
                            # Plot the spot diagram - use scatter or plot with no line
                            FreeCAD.Console.PrintMessage(f"    Plotting data...\n")
                            ax.plot(X, Y, 'o', linestyle='None', markersize=3)
                            
                            # Enable grid for better readability
                            ax.grid(True)
                            
                            # Add labels with proper formatting
                            ax.set_title(f"Spot Diagram - {n} ({len(hl)} rays)")
                            ax.set_xlabel("X position (mm)")
                            ax.set_ylabel("Y position (mm)")
                            
                            # Set equal aspect ratio for accurate spot visualization
                            # Use 'box' adjustable to avoid matplotlib warnings
                            ax.set_aspect('equal', adjustable='box')
                        
                        FreeCAD.Console.PrintMessage(f"    Plot configuration complete\n")
                        
                        plot_count += 1
                        FreeCAD.Console.PrintMessage(
                            f"Generated spot diagram for sensor '{n}' ({len(hl)} rays)\n"
                        )
                    
                    except KeyError as ke:
                        FreeCAD.Console.PrintWarning(
                            f"Sensor '{n}' not found in propagation results. KeyError: {ke}\n"
                        )
                        FreeCAD.Console.PrintWarning(
                            f"Available keys in optical system: {list(s.keys())}\n"
                        )
                        continue
                    except Exception as e:
                        FreeCAD.Console.PrintError(
                            f"Error processing sensor '{n}': {type(e).__name__}: {e}\n"
                        )
                        FreeCAD.Console.PrintError(traceback.format_exc())
                        continue
            
            if plot_count > 0:
                FreeCAD.Console.PrintMessage(
                    f"Successfully generated {plot_count} spot diagram(s)\n"
                )
                FreeCAD.Console.PrintMessage(
                    "Note: Qt errors when using plot toolbar buttons (pan/zoom) are a known issue\n"
                    "in the matplotlib/FreeCAD integration and can be safely ignored.\n"
                )
            else:
                FeedbackHelper.show_error_dialog(
                    "No Plots Generated",
                    "No spot diagrams could be generated.\n\n"
                    "Possible reasons:\n"
                    "• Sensors have no ray hits\n"
                    "• Sensor names don't match propagation results\n"
                    "• Ray propagation may need to be re-run"
                )
            
        except Exception as e:
            # Print full stack trace to console for debugging
            FreeCAD.Console.PrintError("="*60 + "\n")
            FreeCAD.Console.PrintError("REPORTS ERROR - Full Stack Trace:\n")
            FreeCAD.Console.PrintError("="*60 + "\n")
            FreeCAD.Console.PrintError(traceback.format_exc())
            FreeCAD.Console.PrintError("="*60 + "\n")
            
            FeedbackHelper.show_error_dialog(
                "Report Generation Failed",
                FeedbackHelper.format_error(
                    e,
                    "Could not generate reports.\n\n"
                    "Please verify:\n"
                    "• Ray propagation has been completed\n"
                    "• Sensors are properly configured\n"
                    "• Sensor data is available"
                )
            )
