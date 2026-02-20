"""Generic, extensible formatter for component info panel display.

This module provides formatting functionality for pyoptools catalog components
that automatically handles any component type without hardcoded knowledge.
Designed to work with future component types without code changes.
"""


class ComponentInfoFormatter:
    """Generic, extensible formatter for component info panel display.
    
    Automatically handles any component type from pyoptools catalogs without
    hardcoded knowledge of specific component types. Designed to work with
    future component types without code changes.
    """
    
    # Field priority order (higher priority fields shown first)
    FIELD_PRIORITY = {
        'type': 100,
        'description': 95,
        'diameter': 90,
        'radius': 89,
        'focal_length': 88,
        'thickness': 85,
        'material': 84,
        'material_l1': 83,
        'material_l2': 82,
        'curvature_s1': 70,
        'curvature_s2': 69,
        'curvature_s3': 68,
        'size': 65,
        'coating': 60,
        'reflectivity': 58,
        'wavelength': 55,
        # All other fields get default priority of 50
    }
    
    # Units for common field patterns
    UNIT_PATTERNS = {
        'diameter': 'mm',
        'radius': 'mm',
        'thickness': 'mm',
        'focal_length': 'mm',
        'size': 'mm',
        'wavelength': 'nm',
        'angle': '°',
        'reflectivity': '%',
        'curvature': '1/mm',
    }
    
    # Fields to skip in generic display (shown separately or not useful)
    SKIP_FIELDS = {'type', 'glass_catalogs', 'origin', 'description'}
    
    def format_component_info(self, catalog, reference, descriptor, 
                             is_available=None, unavailable_reason=None):
        """Format component descriptor as user-friendly text display.
        
        Generic implementation that works with any component type.
        
        Args:
            catalog: Catalog name (e.g., "thorlabs")
            reference: Part number (e.g., "LA1131-A")
            descriptor: Component descriptor dictionary from pyoptools
            is_available: Whether component materials are available (optional)
            unavailable_reason: Reason if unavailable (optional)
            
        Returns:
            Formatted string for Info panel display
        """
        lines = []
        
        # Header section
        comp_type = descriptor.get('type', 'Unknown')
        human_name = self._to_human_readable(comp_type)
        
        lines.append("═" * 60)
        lines.append(f"{human_name}")
        lines.append(f"Part: {reference}  |  Catalog: {catalog.title()}")
        lines.append("═" * 60)
        lines.append("")
        
        # Description section (if available)
        if 'description' in descriptor and descriptor['description']:
            desc = descriptor['description']
            # Wrap long descriptions
            if len(desc) > 56:
                desc = desc[:56] + "..."
            lines.append(f"Description: {desc}")
            lines.append("")
        
        # Specifications section
        lines.append("Specifications:")
        lines.append("─" * 60)
        
        # Format specifications generically
        self._format_specifications(lines, descriptor)
        
        lines.append("─" * 60)
        lines.append("")
        
        # Availability status (if provided)
        if is_available is not None:
            if is_available:
                lines.append("✓ Available (all materials in library)")
            else:
                reason = unavailable_reason or "Material not found"
                lines.append(f"✗ Unavailable ({reason})")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_specifications(self, lines, descriptor):
        """Format specifications section generically for any component type."""
        # Get all fields except those to skip
        fields = [(k, v) for k, v in descriptor.items() 
                 if k not in self.SKIP_FIELDS and v is not None]
        
        # Sort by priority
        fields.sort(key=lambda x: self.FIELD_PRIORITY.get(x[0], 50), reverse=True)
        
        # Format each field
        for key, value in fields:
            self._format_field(lines, key, value)
    
    def _format_field(self, lines, key, value):
        """Format a single field for display."""
        # Convert key to human-readable label
        label = self._to_human_readable(key)
        
        # Handle different value types
        if isinstance(value, dict):
            # Nested structure (e.g., aspheric surface data)
            lines.append(f"  • {label}:")
            for sub_key, sub_value in value.items():
                if sub_value is not None and not isinstance(sub_value, (dict, list)):
                    sub_label = self._to_human_readable(sub_key)
                    formatted_val = self._format_value(sub_key, sub_value)
                    lines.append(f"      {sub_label}: {formatted_val}")
        
        elif isinstance(value, list):
            # Array values (e.g., size [6.25, 6.25])
            if all(isinstance(x, (int, float)) for x in value):
                # Numeric array - show dimensions
                formatted_vals = [self._format_number(x) for x in value]
                unit = self._get_unit(key)
                lines.append(f"  • {label}: {' x '.join(formatted_vals)} {unit}")
            else:
                # Other arrays - show as list
                lines.append(f"  • {label}: {value}")
        
        else:
            # Simple scalar value
            formatted_val = self._format_value(key, value)
            lines.append(f"  • {label}: {formatted_val}")
    
    def _format_value(self, key, value):
        """Format a value with appropriate precision and units."""
        if isinstance(value, float):
            # Format number with appropriate precision
            formatted = self._format_number(value)
            unit = self._get_unit(key)
            return f"{formatted} {unit}" if unit else formatted
        
        elif isinstance(value, int):
            unit = self._get_unit(key)
            return f"{value} {unit}" if unit else str(value)
        
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        
        elif value is None:
            return "N/A"
        
        else:
            return str(value)
    
    def _format_number(self, value):
        """Format a number with appropriate precision."""
        if abs(value) < 0.001:
            # Very small numbers - use scientific notation
            return f"{value:.2e}"
        elif abs(value) < 1.0:
            # Small numbers - 4 decimal places
            return f"{value:.4f}".rstrip('0').rstrip('.')
        elif abs(value) < 10.0:
            # Single digit - 2 decimal places
            return f"{value:.2f}".rstrip('0').rstrip('.')
        elif abs(value) < 100.0:
            # Two digits - 1 decimal place
            return f"{value:.1f}".rstrip('0').rstrip('.')
        else:
            # Larger numbers - no decimals unless needed
            if value == int(value):
                return str(int(value))
            return f"{value:.1f}".rstrip('0').rstrip('.')
    
    def _get_unit(self, field_name):
        """Get appropriate unit for a field name."""
        # Check exact matches first
        if field_name in self.UNIT_PATTERNS:
            return self.UNIT_PATTERNS[field_name]
        
        # Check patterns in field name
        field_lower = field_name.lower()
        for pattern, unit in self.UNIT_PATTERNS.items():
            if pattern in field_lower:
                return unit
        
        return ""
    
    def _to_human_readable(self, text):
        """Convert snake_case or PascalCase to Human Readable.
        
        Examples:
            'SphericalLens' -> 'Spherical Lens'
            'material_l1' -> 'Material L1'
            'curvature_s1' -> 'Curvature S1'
            'air_gap' -> 'Air Gap'
        """
        # Handle PascalCase (insert spaces before capitals)
        import re
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Handle snake_case (replace underscores with spaces)
        text = text.replace('_', ' ')
        
        # Capitalize words
        words = text.split()
        capitalized = []
        for word in words:
            # Keep known acronyms uppercase
            if word.upper() in ['S1', 'S2', 'S3', 'S4', 'L1', 'L2', 'NA', 'ROC']:
                capitalized.append(word.upper())
            else:
                capitalized.append(word.capitalize())
        
        return ' '.join(capitalized)
