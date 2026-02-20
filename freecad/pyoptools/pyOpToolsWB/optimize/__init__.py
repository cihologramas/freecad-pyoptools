# -*- coding: utf-8 -*-
"""Optical system optimization module.

This module provides tools for optimizing optical component positions
to achieve various optical goals (collimation, spot size, etc.).

Organization:
    - merit_functions.py: Merit functions for different optimization goals
    - optimization_worker.py: Background worker thread for scipy optimization
    - optimize_gui.py: Qt GUI for optimization dialog
    - optimize_menu.py: FreeCAD menu integration
"""

from .optimize_menu import OptimizeMenu

__all__ = ['OptimizeMenu']
