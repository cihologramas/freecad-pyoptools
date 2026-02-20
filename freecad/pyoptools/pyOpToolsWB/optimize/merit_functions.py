# -*- coding: utf-8 -*-
"""Merit functions for optical system optimization.

This module provides various merit functions that calculate optical quality metrics.
These functions are used by scipy.optimize.minimize to find optimal component positions:
    - collimation_error: Calculate angular spread (std of transverse direction components)
    - spot_size: Calculate radial spread from centroid
    - x_axis_spread: Calculate X-axis spread
    - y_axis_spread: Calculate Y-axis spread

All functions share a common setup via _setup_system_and_propagate().

The merit functions accept a displacement vector and move the component by that
displacement before evaluating the optical system performance.

Typical usage:
    # Optimization moves component along direction vector
    displacement = param * direction
    merit = collimation_error(displacement, "Lens1", "Sensor1")
    result = minimize(lambda x: merit_func(x * direction), 0, ...)
"""

# Standard library imports
from typing import Tuple, List

# Third-party imports
from numpy import std, array, sqrt, abs

# Local application imports
from ..pyoptoolshelpers import getActiveSystem

__all__ = [
    'collimation_error',
    'spot_size',
    'x_axis_spread',
    'y_axis_spread',
]

def _setup_system_and_propagate(
    displacement, 
    element_label: str, 
    sensor_label: str, 
) -> Tuple[List, List, List, List]:
    """Common setup: apply position, propagate rays, get optical data.
    
    This helper function handles the common workflow shared by all merit functions:
    1. Get the active optical system and rays
    2. Update the specified component's position to the given absolute position
    3. Add rays to the system and propagate
    4. Extract optical path data and direction vectors from the sensor
    
    Args:
        displacement: Displacement vector to apply to element position
        element_label: Label of optical component to optimize
        sensor_label: Label of sensor to measure results
        
    Returns:
        Tuple of (X, Y, optical_path_distances, direction_vectors) from sensor data
        
    Raises:
        KeyError: If element or sensor label not found in system
        ValueError: If sensor returns no optical data
    """
    system, rays = getActiveSystem()
    
    # Update system with new position
    try:
        component, initial_pos, direction = system.complist[element_label]
        position = (initial_pos + displacement)
        system.complist[element_label] = component, position, direction
    except KeyError:
        # we assume the component is a ray source and not in complist so we update the position of the ray source directly
        for ray in rays:
            if ray.label == element_label:
                initial_pos = ray.origin
                ray.origin = initial_pos + displacement

    # Propagate rays through system
    system.ray_add(rays)
    system.propagate()
    
    # Get optical path data from sensor
    X, Y, optical_path_distances = system[sensor_label][0].get_optical_path_data()
    
    # TODO: Extract direction vectors from hit_list
    # This functionality should be moved to pyoptools (e.g., sensor.get_direction_data())
    # For now, we extract them manually here
    # hit_list contains tuples of (hit_point, ray)
    sensor = system[sensor_label][0]
    direction_vectors = []
    for hit_point, ray in sensor.hit_list:
        direction_vectors.append(ray.direction)
    
    return X, Y, optical_path_distances, direction_vectors


def collimation_error(
    position, 
    element_label: str, 
    sensor_label: str
) -> float:
    """Calculate collimation error (angular spread).
    
    Collimation quality is measured by the standard deviation of the
    transverse components of ray direction vectors. For perfect collimation
    along the z-axis, all rays should have direction (0, 0, 1), so the
    std of (dx² + dy²) should be 0.
    
    Args:
        position: Displacement vector to apply to element position
        element_label: Label of optical component to optimize
        sensor_label: Label of sensor to measure results
        
    Returns:
        Standard deviation of (dx² + dy²) for direction vectors (lower is better)
    """
    _, _, _, direction_vectors = _setup_system_and_propagate(
        position, element_label, sensor_label
    )
    
    # Calculate dx² + dy² for each direction vector
    # For perfect collimation (0, 0, 1), this should be 0
    transverse_squares = []
    for direction in direction_vectors:
        dx, dy, dz = direction
        transverse_squares.append(dx**2 + dy**2)
    
    # Return std of transverse components
    result = std(transverse_squares)
    print(f"Collimation error (std of dx²+dy²): {result}")
    return result


def spot_size(
    position, 
    element_label: str, 
    sensor_label: str, 
) -> float:
    """Calculate spot size (radial spread).
    
    Spot size is measured as the mean radial distance from the centroid
    of the ray distribution on the sensor.
    
    Args:
        position: Displacement vector to apply to element position
        element_label: Label of optical component to optimize
        sensor_label: Label of sensor to measure results
        
    Returns:
        Mean radial distance from centroid (lower is better)
    """
    X, Y, _, _ = _setup_system_and_propagate(
        position, element_label, sensor_label
    )
    
    # Convert to numpy arrays and center at origin
    X_arr = array(X)
    Y_arr = array(Y)
    X_centered = X_arr - X_arr.mean()
    Y_centered = Y_arr - Y_arr.mean()
    
    # Calculate radial distance from centroid
    radial_distance = sqrt(X_centered**2 + Y_centered**2)
    
    return radial_distance.mean()


def x_axis_spread(
    position, 
    element_label: str, 
    sensor_label: str, 
) -> float:
    """Calculate X-axis spread.
    
    Measures the mean absolute deviation from the X centroid.
    Useful for optimizing horizontal focus or alignment.
    
    Args:
        position: Displacement vector to apply to element position
        element_label: Label of optical component to optimize
        sensor_label: Label of sensor to measure results
        
    Returns:
        Mean absolute X deviation from centroid (lower is better)
    """
    X, _, _, _ = _setup_system_and_propagate(
        position, element_label, sensor_label
    )
    
    # Convert to numpy array and center
    X_arr = array(X)
    X_centered = X_arr - X_arr.mean()
    
    # Return mean absolute deviation
    return abs(X_centered).mean()


def y_axis_spread(
    position, 
    element_label: str, 
    sensor_label: str, 
) -> float:
    """Calculate Y-axis spread.
    
    Measures the mean absolute deviation from the Y centroid.
    Useful for optimizing vertical focus or alignment.
    
    Args:
        position: Displacement vector to apply to element position
        element_label: Label of optical component to optimize
        sensor_label: Label of sensor to measure results
        
    Returns:
        Mean absolute Y deviation from centroid (lower is better)
    """
    _, Y, _, _ = _setup_system_and_propagate(
        position, element_label, sensor_label
    )
    
    # Convert to numpy array and center
    Y_arr = array(Y)
    Y_centered = Y_arr - Y_arr.mean()
    
    # Return mean absolute deviation
    return abs(Y_centered).mean()
