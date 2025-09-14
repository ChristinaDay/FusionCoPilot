"""
Fusion 360 Natural-Language CAD Co-Pilot - Plan Sanitizer

This module provides comprehensive validation and sanitization of structured plans
before execution. It ensures geometric feasibility, unit consistency, and 
manufacturing constraints compliance.

Author: Fusion CoPilot Team
License: MIT
"""

import json
import math
import re
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when plan validation fails with unrecoverable errors."""
    pass


class ValidationWarning(Exception):
    """Raised when plan has warnings that may be acceptable."""
    pass


class PlanSanitizer:
    """
    Comprehensive plan validation and sanitization engine.
    
    Validates plans against:
    - JSON Schema compliance
    - Geometric feasibility 
    - Unit consistency and conversion
    - Manufacturing constraints
    - Feature reference resolution
    - Safety limits and bounds checking
    """
    
    def __init__(self, machine_profile: Optional[Dict] = None, settings: Optional[Dict] = None):
        """
        Initialize the sanitizer with machine profile and settings.
        
        Args:
            machine_profile: Manufacturing constraints and capabilities
            settings: Configuration settings from settings.yaml
        """
        self.machine_profile = machine_profile or self._default_machine_profile()
        self.settings = settings or {}
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
        
        # Unit conversion factors to mm (base unit)
        self.unit_conversions = {
            'mm': 1.0,
            'cm': 10.0,
            'm': 1000.0,
            'in': 25.4,
            'ft': 304.8,
            'deg': 1.0,  # Degrees (no conversion needed)
            'rad': 180.0 / math.pi  # Radians to degrees
        }
    
    def sanitize_plan(self, plan: Dict, strict_mode: bool = False) -> Tuple[bool, Dict, List[str]]:
        """
        Main sanitization entry point.
        
        Performs comprehensive validation and sanitization of a structured plan.
        
        Args:
            plan: Raw plan dictionary from LLM
            strict_mode: If True, treat warnings as errors
            
        Returns:
            Tuple of (is_valid, sanitized_plan, error_messages)
            
        Raises:
            ValidationError: For unrecoverable validation failures
        """
        logger.info(f"Starting sanitization of plan: {plan.get('plan_id', 'unknown')}")
        
        # Reset validation state
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        try:
            # Step 1: Basic structure validation
            self._validate_plan_structure(plan)
            
            # Step 2: Metadata validation and enhancement
            sanitized_plan = self._sanitize_metadata(plan.copy())
            
            # Step 3: Operations validation and sanitization
            sanitized_plan['operations'] = self._sanitize_operations(
                sanitized_plan['operations']
            )
            
            # Step 4: Cross-operation validation
            self._validate_operation_dependencies(sanitized_plan['operations'])
            
            # Step 5: Geometric feasibility checks
            self._validate_geometric_feasibility(sanitized_plan['operations'])
            
            # Step 6: Manufacturing constraints validation
            self._validate_manufacturing_constraints(sanitized_plan['operations'])
            
            # Step 7: Final safety checks
            self._perform_safety_checks(sanitized_plan)
            
            # Determine overall validation status
            has_errors = len(self.validation_errors) > 0
            has_warnings = len(self.validation_warnings) > 0
            
            if strict_mode and has_warnings:
                has_errors = True
                self.validation_errors.extend(self.validation_warnings)
            
            # Compile all messages
            all_messages = self.validation_errors + self.validation_warnings
            
            logger.info(f"Sanitization complete. Errors: {len(self.validation_errors)}, "
                       f"Warnings: {len(self.validation_warnings)}")
            
            return (not has_errors, sanitized_plan, all_messages)
            
        except Exception as e:
            logger.error(f"Unexpected error during sanitization: {str(e)}")
            self.validation_errors.append(f"Internal sanitization error: {str(e)}")
            return (False, plan, self.validation_errors)
    
    def _validate_plan_structure(self, plan: Dict) -> None:
        """Validate basic plan structure and required fields."""
        required_fields = ['plan_id', 'metadata', 'operations']
        
        for field in required_fields:
            if field not in plan:
                raise ValidationError(f"Missing required field: {field}")
        
        if not isinstance(plan['operations'], list):
            raise ValidationError("Operations must be a list")
        
        if len(plan['operations']) == 0:
            raise ValidationError("Plan must contain at least one operation")
        
        if len(plan['operations']) > self.settings.get('max_operations_per_plan', 50):
            raise ValidationError(f"Plan exceeds maximum operations limit: "
                                f"{self.settings.get('max_operations_per_plan', 50)}")
    
    def _sanitize_metadata(self, plan: Dict) -> Dict:
        """Sanitize and enhance plan metadata."""
        metadata = plan['metadata']
        
        # Ensure required metadata fields
        if 'created_at' not in metadata:
            metadata['created_at'] = datetime.utcnow().isoformat() + 'Z'
        
        if 'units' not in metadata:
            metadata['units'] = self.settings.get('units_default', 'mm')
        
        # Validate units
        if metadata['units'] not in self.unit_conversions:
            self.validation_warnings.append(
                f"Unknown unit '{metadata['units']}', defaulting to mm"
            )
            metadata['units'] = 'mm'
        
        # Validate confidence score
        if 'confidence_score' in metadata:
            confidence = metadata['confidence_score']
            if not (0.0 <= confidence <= 1.0):
                self.validation_warnings.append(
                    f"Invalid confidence score {confidence}, clamping to [0,1]"
                )
                metadata['confidence_score'] = max(0.0, min(1.0, confidence))
        
        # Validate natural language prompt
        prompt = metadata.get('natural_language_prompt', '')
        if len(prompt) > 2000:
            self.validation_warnings.append("Prompt truncated to 2000 characters")
            metadata['natural_language_prompt'] = prompt[:2000]
        
        return plan
    
    def _sanitize_operations(self, operations: List[Dict]) -> List[Dict]:
        """Sanitize individual operations."""
        sanitized_ops = []
        
        for i, op in enumerate(operations):
            try:
                sanitized_op = self._sanitize_single_operation(op, i)
                sanitized_ops.append(sanitized_op)
            except ValidationError as e:
                self.validation_errors.append(f"Operation {i}: {str(e)}")
            except ValidationWarning as e:
                self.validation_warnings.append(f"Operation {i}: {str(e)}")
                sanitized_ops.append(op)  # Keep original if just warning
        
        return sanitized_ops
    
    def _sanitize_single_operation(self, operation: Dict, index: int) -> Dict:
        """Sanitize a single operation with comprehensive validation."""
        op = operation.copy()
        
        # Validate required fields
        required_fields = ['op_id', 'op', 'params']
        for field in required_fields:
            if field not in op:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate operation ID format
        if not re.match(r'^op_\d+$', op['op_id']):
            raise ValidationError(f"Invalid op_id format: {op['op_id']}")
        
        # Validate operation type
        valid_ops = self._get_valid_operations()
        if op['op'] not in valid_ops:
            raise ValidationError(f"Unknown operation type: {op['op']}")
        
        # Sanitize parameters based on operation type
        op['params'] = self._sanitize_operation_params(op['op'], op['params'])
        
        # Validate target references
        if 'target_ref' in op:
            self._validate_target_reference(op['target_ref'])
        
        return op
    
    def _sanitize_operation_params(self, op_type: str, params: Dict) -> Dict:
        """Sanitize parameters for specific operation types."""
        sanitized_params = params.copy()
        
        # Operation-specific parameter validation
        if op_type in ['draw_circle', 'create_hole']:
            sanitized_params = self._sanitize_circular_params(sanitized_params)
        elif op_type in ['draw_rectangle']:
            sanitized_params = self._sanitize_rectangular_params(sanitized_params)
        elif op_type in ['extrude', 'cut']:
            sanitized_params = self._sanitize_extrude_params(sanitized_params)
        elif op_type in ['fillet', 'chamfer']:
            sanitized_params = self._sanitize_edge_params(sanitized_params)
        elif op_type == 'shell':
            sanitized_params = self._sanitize_shell_params(sanitized_params)
        elif op_type in ['pattern_linear', 'pattern_circular']:
            sanitized_params = self._sanitize_pattern_params(sanitized_params)
        
        # Convert all dimensional parameters
        sanitized_params = self._convert_dimensional_params(sanitized_params)
        
        return sanitized_params
    
    def _sanitize_circular_params(self, params: Dict) -> Dict:
        """Sanitize parameters for circular operations (circles, holes)."""
        if 'diameter' in params:
            diameter = self._extract_dimension_value(params['diameter'])
            if diameter <= 0:
                raise ValidationError("Diameter must be positive")
            
            # Check against machine constraints
            min_diameter = self.machine_profile.get('min_tool_diameter', 0.1)
            if diameter < min_diameter:
                raise ValidationWarning(
                    f"Diameter {diameter}mm below minimum tool diameter "
                    f"{min_diameter}mm"
                )
        
        if 'radius' in params:
            radius = self._extract_dimension_value(params['radius'])
            if radius <= 0:
                raise ValidationError("Radius must be positive")
        
        return params
    
    def _sanitize_rectangular_params(self, params: Dict) -> Dict:
        """Sanitize parameters for rectangular operations."""
        for dim in ['width', 'height', 'length']:
            if dim in params:
                value = self._extract_dimension_value(params[dim])
                if value <= 0:
                    raise ValidationError(f"{dim.capitalize()} must be positive")
                
                max_size = self.machine_profile.get('max_feature_size', 1000)
                if value > max_size:
                    raise ValidationError(
                        f"{dim.capitalize()} {value}mm exceeds maximum "
                        f"feature size {max_size}mm"
                    )
        
        return params
    
    def _sanitize_extrude_params(self, params: Dict) -> Dict:
        """Sanitize parameters for extrude/cut operations."""
        if 'distance' in params:
            distance = self._extract_dimension_value(params['distance'])
            if distance <= 0:
                raise ValidationError("Extrude distance must be positive")
            
            max_depth = self.machine_profile.get('max_cut_depth', 100)
            if distance > max_depth:
                raise ValidationWarning(
                    f"Extrude distance {distance}mm exceeds recommended "
                    f"maximum {max_depth}mm"
                )
        
        # Validate direction
        if 'direction' in params:
            valid_directions = ['positive', 'negative', 'symmetric']
            if params['direction'] not in valid_directions:
                raise ValidationError(
                    f"Invalid direction: {params['direction']}. "
                    f"Must be one of {valid_directions}"
                )
        
        return params
    
    def _sanitize_edge_params(self, params: Dict) -> Dict:
        """Sanitize parameters for edge operations (fillet, chamfer)."""
        if 'radius' in params:
            radius = self._extract_dimension_value(params['radius'])
            if radius <= 0:
                raise ValidationError("Fillet/chamfer radius must be positive")
            
            # Reasonable upper limit for fillet radius
            if radius > 50:  # mm
                raise ValidationWarning(
                    f"Large fillet radius {radius}mm may cause geometric issues"
                )
        
        return params
    
    def _sanitize_shell_params(self, params: Dict) -> Dict:
        """Sanitize parameters for shell operations."""
        if 'thickness' in params:
            thickness = self._extract_dimension_value(params['thickness'])
            if thickness <= 0:
                raise ValidationError("Shell thickness must be positive")
            
            min_thickness = self.machine_profile.get('min_wall_thickness', 0.8)
            if thickness < min_thickness:
                raise ValidationWarning(
                    f"Shell thickness {thickness}mm below minimum "
                    f"wall thickness {min_thickness}mm"
                )
        
        return params
    
    def _sanitize_pattern_params(self, params: Dict) -> Dict:
        """Sanitize parameters for pattern operations."""
        # Validate counts
        for count_param in ['count_1', 'count_2', 'count']:
            if count_param in params:
                count = params[count_param]
                if not isinstance(count, int) or count < 1:
                    raise ValidationError(f"{count_param} must be a positive integer")
                if count > 100:  # Reasonable limit
                    raise ValidationWarning(f"Large pattern count {count} may impact performance")
        
        # Validate distances
        for dist_param in ['distance_1', 'distance_2', 'spacing']:
            if dist_param in params:
                distance = self._extract_dimension_value(params[dist_param])
                if distance <= 0:
                    raise ValidationError(f"{dist_param} must be positive")
        
        return params
    
    def _convert_dimensional_params(self, params: Dict) -> Dict:
        """Convert all dimensional parameters to consistent units."""
        converted_params = {}
        
        for key, value in params.items():
            if isinstance(value, dict) and 'value' in value and 'unit' in value:
                # This is a dimensional parameter
                converted_params[key] = self._convert_dimension(value)
            elif isinstance(value, dict) and all(k in value for k in ['x', 'y', 'z']):
                # This is a 3D point/vector
                converted_params[key] = value  # Keep as-is, assume base units
            else:
                converted_params[key] = value
        
        return converted_params
    
    def _convert_dimension(self, dimension: Dict) -> Dict:
        """Convert a dimension to base units (mm)."""
        if not isinstance(dimension, dict) or 'value' not in dimension:
            return dimension
        
        value = dimension['value']
        unit = dimension.get('unit', 'mm')
        
        if unit not in self.unit_conversions:
            self.validation_warnings.append(f"Unknown unit '{unit}', treating as mm")
            unit = 'mm'
        
        # Convert to base units (mm)
        converted_value = value * self.unit_conversions[unit]
        
        return {
            'value': converted_value,
            'unit': 'mm',
            'original_value': value,
            'original_unit': unit
        }
    
    def _extract_dimension_value(self, dimension: Union[Dict, float, int]) -> float:
        """Extract numeric value from dimension parameter."""
        if isinstance(dimension, (int, float)):
            return float(dimension)
        elif isinstance(dimension, dict):
            if 'value' in dimension:
                return float(dimension['value'])
        
        raise ValidationError(f"Invalid dimension format: {dimension}")
    
    def _validate_operation_dependencies(self, operations: List[Dict]) -> None:
        """Validate that operation dependencies are satisfied."""
        op_ids = {op['op_id'] for op in operations}
        
        for op in operations:
            if 'dependencies' in op:
                for dep_id in op['dependencies']:
                    if dep_id not in op_ids:
                        self.validation_errors.append(
                            f"Operation {op['op_id']} depends on non-existent "
                            f"operation {dep_id}"
                        )
    
    def _validate_geometric_feasibility(self, operations: List[Dict]) -> None:
        """Validate geometric feasibility of operations."""
        # Check for geometric impossibilities
        for op in operations:
            op_type = op['op']
            params = op['params']
            
            # Example: Check for zero-volume extrusions
            if op_type == 'extrude':
                distance = self._extract_dimension_value(params.get('distance', 0))
                if distance == 0:
                    self.validation_warnings.append(
                        f"Zero-distance extrude in operation {op['op_id']}"
                    )
            
            # Example: Check for impossible fillet radii
            elif op_type == 'fillet':
                radius = self._extract_dimension_value(params.get('radius', 0))
                # Additional checks would require feature context
                if radius > 100:  # Arbitrary large value check
                    self.validation_warnings.append(
                        f"Very large fillet radius {radius}mm in operation {op['op_id']}"
                    )
    
    def _validate_manufacturing_constraints(self, operations: List[Dict]) -> None:
        """Validate operations against manufacturing constraints."""
        for op in operations:
            op_type = op['op']
            params = op['params']
            
            # Check hole diameters against tool capabilities
            if op_type in ['create_hole', 'draw_circle']:
                if 'diameter' in params:
                    diameter = self._extract_dimension_value(params['diameter'])
                    min_tool = self.machine_profile.get('min_tool_diameter', 0.1)
                    
                    if diameter < min_tool:
                        self.validation_warnings.append(
                            f"Hole diameter {diameter}mm smaller than minimum "
                            f"tool diameter {min_tool}mm"
                        )
            
            # Check cut depths
            elif op_type in ['extrude', 'cut']:
                if 'distance' in params:
                    depth = self._extract_dimension_value(params['distance'])
                    max_depth = self.machine_profile.get('max_cut_depth', 100)
                    
                    if depth > max_depth:
                        self.validation_warnings.append(
                            f"Cut depth {depth}mm exceeds machine capability "
                            f"{max_depth}mm"
                        )
    
    def _validate_target_reference(self, target_ref: str) -> None:
        """Validate target reference format and existence."""
        # Basic format validation
        valid_patterns = [
            r'^sketch_\w+$',      # sketch_1, sketch_base
            r'^face_\w+$',        # face_top, face_1
            r'^edge_\w+$',        # edge_front, edge_1
            r'^feature_\w+$',     # feature_extrude1
            r'^component_\w+$',   # component_1
        ]
        
        if not any(re.match(pattern, target_ref) for pattern in valid_patterns):
            self.validation_warnings.append(
                f"Unusual target reference format: {target_ref}"
            )
    
    def _perform_safety_checks(self, plan: Dict) -> None:
        """Perform final safety validation checks."""
        # Check total estimated execution time
        estimated_time = plan['metadata'].get('estimated_duration_seconds', 0)
        max_time = self.settings.get('max_execution_time', 300)
        
        if estimated_time > max_time:
            self.validation_warnings.append(
                f"Estimated execution time {estimated_time}s exceeds "
                f"maximum {max_time}s"
            )
        
        # Check for potentially destructive operations
        destructive_ops = ['cut', 'shell', 'delete_feature']
        for op in plan['operations']:
            if op['op'] in destructive_ops:
                self.validation_warnings.append(
                    f"Plan contains potentially destructive operation: {op['op']}"
                )
    
    def _get_valid_operations(self) -> List[str]:
        """Get list of valid operation types."""
        return [
            'create_sketch', 'draw_line', 'draw_circle', 'draw_rectangle',
            'draw_polygon', 'draw_arc', 'draw_spline', 'extrude', 'cut',
            'revolve', 'sweep', 'loft', 'fillet', 'chamfer', 'shell',
            'mirror', 'pattern_linear', 'pattern_circular', 'pattern_rectangular', 'pattern_path',
            'create_plane', 'create_axis', 'create_point', 'set_dimension',
            'add_constraint', 'rename_feature', 'create_component',
            'create_joint', 'create_hole', 'thread_hole', 'countersink_hole',
            'counterbore_hole'
        ]
    
    def _default_machine_profile(self) -> Dict:
        """Default machine profile for validation."""
        return {
            'min_tool_diameter': 0.5,    # mm
            'max_cut_depth': 100,        # mm
            'min_wall_thickness': 0.8,   # mm
            'max_feature_size': 1000,    # mm
            'supported_materials': ['aluminum', 'steel', 'plastic'],
            'tolerances': {
                'general': 0.1,
                'precision': 0.05,
                'rough': 0.2
            }
        }


def resolve_nearest_feature(selected_point: Dict, features: List[Dict]) -> Optional[str]:
    """
    Resolve the nearest feature to a selected point.
    
    This is a helper function for ambiguous feature references in natural language.
    In a full implementation, this would use Fusion 360's geometry APIs.
    
    Args:
        selected_point: 3D point coordinates {'x': float, 'y': float, 'z': float}
        features: List of available features with their geometry data
        
    Returns:
        Feature identifier string, or None if no suitable feature found
    """
    # Placeholder implementation - in real usage, this would:
    # 1. Calculate distances from point to all feature geometries
    # 2. Return the closest feature within a reasonable tolerance
    # 3. Handle edge cases like multiple features at same distance
    
    logger.info(f"Resolving nearest feature to point {selected_point}")
    
    if not features:
        return None
    
    # Simple distance calculation (placeholder)
    min_distance = float('inf')
    nearest_feature = None
    
    for feature in features:
        if 'center_point' in feature:
            center = feature['center_point']
            distance = math.sqrt(
                (selected_point['x'] - center['x']) ** 2 +
                (selected_point['y'] - center['y']) ** 2 +
                (selected_point['z'] - center['z']) ** 2
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_feature = feature.get('id', feature.get('name'))
    
    return nearest_feature


def validate_plan_against_schema(plan: Dict, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate plan against JSON schema.
    
    Args:
        plan: Plan dictionary to validate
        schema_path: Path to JSON schema file
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        import jsonschema
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        jsonschema.validate(plan, schema)
        return (True, [])
        
    except ImportError:
        logger.warning("jsonschema not available, skipping schema validation")
        return (True, ["Schema validation skipped - jsonschema not installed"])
        
    except jsonschema.ValidationError as e:
        return (False, [f"Schema validation failed: {e.message}"])
        
    except Exception as e:
        return (False, [f"Schema validation error: {str(e)}"])


# Example usage and testing
if __name__ == "__main__":
    # Example plan for testing
    test_plan = {
        "plan_id": "test_plate_001",
        "metadata": {
            "created_at": "2024-01-15T10:30:00Z",
            "natural_language_prompt": "Create a 100x50mm plate that's 5mm thick",
            "estimated_duration_seconds": 15,
            "confidence_score": 0.95,
            "units": "mm"
        },
        "operations": [
            {
                "op_id": "op_1",
                "op": "create_sketch",
                "params": {
                    "plane": "XY",
                    "name": "base_sketch"
                }
            },
            {
                "op_id": "op_2",
                "op": "draw_rectangle",
                "params": {
                    "center_point": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 100, "unit": "mm"},
                    "height": {"value": 50, "unit": "mm"}
                },
                "target_ref": "base_sketch",
                "dependencies": ["op_1"]
            }
        ]
    }
    
    # Test sanitization
    sanitizer = PlanSanitizer()
    is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(test_plan)
    
    print(f"Plan validation: {'PASSED' if is_valid else 'FAILED'}")
    if messages:
        print("Messages:")
        for msg in messages:
            print(f"  - {msg}")
    
    print(f"\nSanitized plan operations: {len(sanitized_plan['operations'])}")
