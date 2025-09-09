"""
Test suite for the Fusion 360 Co-Pilot Plan Sanitizer

Tests validation, sanitization, and error handling for structured plans.

Author: Fusion CoPilot Team
License: MIT
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sanitizer import PlanSanitizer, ValidationError, ValidationWarning


class TestPlanSanitizer:
    """Test cases for the PlanSanitizer class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.machine_profile = {
            'min_tool_diameter': 0.5,
            'max_cut_depth': 100,
            'min_wall_thickness': 0.8,
            'max_feature_size': 1000
        }
        
        self.settings = {
            'max_operations_per_plan': 50,
            'units_default': 'mm'
        }
        
        self.sanitizer = PlanSanitizer(self.machine_profile, self.settings)
    
    def test_valid_simple_plan(self):
        """Test sanitization of a valid simple plan."""
        plan = {
            "plan_id": "test_001",
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "natural_language_prompt": "Create a simple plate",
                "estimated_duration_seconds": 15,
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
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is True
        assert len(messages) == 0
        assert sanitized_plan['plan_id'] == "test_001"
        assert len(sanitized_plan['operations']) == 2
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        plan = {
            "plan_id": "test_002",
            "metadata": {
                "natural_language_prompt": "Test prompt"
            }
            # Missing operations field
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("Missing required field: operations" in msg for msg in messages)
    
    def test_empty_operations_list(self):
        """Test handling of empty operations list."""
        plan = {
            "plan_id": "test_003",
            "metadata": {
                "natural_language_prompt": "Empty plan"
            },
            "operations": []
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("must contain at least one operation" in msg for msg in messages)
    
    def test_too_many_operations(self):
        """Test handling of plans with too many operations."""
        operations = []
        for i in range(60):  # Exceeds max of 50
            operations.append({
                "op_id": f"op_{i}",
                "op": "create_sketch",
                "params": {"plane": "XY"}
            })
        
        plan = {
            "plan_id": "test_004",
            "metadata": {
                "natural_language_prompt": "Too many operations"
            },
            "operations": operations
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("exceeds maximum operations limit" in msg for msg in messages)
    
    def test_invalid_operation_type(self):
        """Test handling of invalid operation types."""
        plan = {
            "plan_id": "test_005",
            "metadata": {
                "natural_language_prompt": "Invalid operation"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "invalid_operation_type",
                    "params": {}
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("Unknown operation type: invalid_operation_type" in msg for msg in messages)
    
    def test_unit_conversion(self):
        """Test unit conversion functionality."""
        plan = {
            "plan_id": "test_006",
            "metadata": {
                "natural_language_prompt": "Test unit conversion",
                "units": "in"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "draw_rectangle",
                    "params": {
                        "width": {"value": 2, "unit": "in"},
                        "height": {"value": 1, "unit": "in"}
                    }
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is True
        
        # Check that dimensions were converted to mm
        width_param = sanitized_plan['operations'][0]['params']['width']
        assert width_param['value'] == 2 * 25.4  # 2 inches to mm
        assert width_param['unit'] == 'mm'
        assert width_param['original_value'] == 2
        assert width_param['original_unit'] == 'in'
    
    def test_negative_dimensions(self):
        """Test handling of negative dimensions."""
        plan = {
            "plan_id": "test_007",
            "metadata": {
                "natural_language_prompt": "Negative dimensions test"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "draw_rectangle",
                    "params": {
                        "width": {"value": -10, "unit": "mm"},
                        "height": {"value": 20, "unit": "mm"}
                    }
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("Width must be positive" in msg for msg in messages)
    
    def test_hole_diameter_validation(self):
        """Test hole diameter validation against machine constraints."""
        plan = {
            "plan_id": "test_008",
            "metadata": {
                "natural_language_prompt": "Small hole test"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_hole",
                    "params": {
                        "diameter": {"value": 0.1, "unit": "mm"},  # Smaller than min_tool_diameter
                        "center_point": {"x": 0, "y": 0, "z": 0}
                    }
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        # Should be valid but with warnings
        assert is_valid is True
        assert any("below minimum tool diameter" in msg for msg in messages)
    
    def test_large_feature_size_warning(self):
        """Test warning for very large features."""
        plan = {
            "plan_id": "test_009",
            "metadata": {
                "natural_language_prompt": "Large feature test"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "draw_rectangle",
                    "params": {
                        "width": {"value": 2000, "unit": "mm"},  # Exceeds max_feature_size
                        "height": {"value": 100, "unit": "mm"}
                    }
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("exceeds maximum feature size" in msg for msg in messages)
    
    def test_operation_dependencies(self):
        """Test operation dependency validation."""
        plan = {
            "plan_id": "test_010",
            "metadata": {
                "natural_language_prompt": "Dependency test"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "extrude",
                    "params": {
                        "distance": {"value": 10, "unit": "mm"}
                    },
                    "dependencies": ["op_nonexistent"]  # Invalid dependency
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("depends on non-existent operation" in msg for msg in messages)
    
    def test_shell_thickness_validation(self):
        """Test shell thickness validation."""
        plan = {
            "plan_id": "test_011",
            "metadata": {
                "natural_language_prompt": "Shell thickness test"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "shell",
                    "params": {
                        "thickness": {"value": 0.1, "unit": "mm"}  # Below min_wall_thickness
                    }
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is True  # Valid but with warning
        assert any("below minimum wall thickness" in msg for msg in messages)
    
    def test_confidence_score_clamping(self):
        """Test confidence score validation and clamping."""
        plan = {
            "plan_id": "test_012",
            "metadata": {
                "natural_language_prompt": "Confidence test",
                "confidence_score": 1.5  # Invalid score > 1.0
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch",
                    "params": {"plane": "XY"}
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is True
        assert sanitized_plan['metadata']['confidence_score'] == 1.0
        assert any("confidence score" in msg and "clamping" in msg for msg in messages)
    
    def test_strict_mode(self):
        """Test strict mode treating warnings as errors."""
        plan = {
            "plan_id": "test_013",
            "metadata": {
                "natural_language_prompt": "Strict mode test"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_hole",
                    "params": {
                        "diameter": {"value": 0.1, "unit": "mm"}  # Will generate warning
                    }
                }
            ]
        }
        
        # Test with strict mode off (default)
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan, strict_mode=False)
        assert is_valid is True
        
        # Test with strict mode on
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan, strict_mode=True)
        assert is_valid is False  # Warning treated as error
    
    def test_pattern_parameter_validation(self):
        """Test pattern parameter validation."""
        plan = {
            "plan_id": "test_014",
            "metadata": {
                "natural_language_prompt": "Pattern validation test"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "pattern_linear",
                    "params": {
                        "count_1": 0,  # Invalid count
                        "distance_1": {"value": -5, "unit": "mm"}  # Invalid distance
                    }
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("must be a positive integer" in msg for msg in messages)
        assert any("must be positive" in msg for msg in messages)
    
    def test_unknown_unit_handling(self):
        """Test handling of unknown units."""
        plan = {
            "plan_id": "test_015",
            "metadata": {
                "natural_language_prompt": "Unknown unit test",
                "units": "unknown_unit"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "draw_rectangle",
                    "params": {
                        "width": {"value": 10, "unit": "unknown_unit"},
                        "height": {"value": 5, "unit": "mm"}
                    }
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is True
        assert any("Unknown unit" in msg for msg in messages)
        # Should default to mm
        assert sanitized_plan['metadata']['units'] == 'mm'


class TestUtilityFunctions:
    """Test utility functions in the sanitizer module."""
    
    def test_resolve_nearest_feature(self):
        """Test the resolve_nearest_feature function."""
        from sanitizer import resolve_nearest_feature
        
        selected_point = {"x": 10, "y": 10, "z": 0}
        features = [
            {
                "id": "feature_1",
                "center_point": {"x": 5, "y": 5, "z": 0}
            },
            {
                "id": "feature_2", 
                "center_point": {"x": 15, "y": 15, "z": 0}
            }
        ]
        
        nearest = resolve_nearest_feature(selected_point, features)
        assert nearest == "feature_2"  # Closer to (10,10)
    
    def test_resolve_nearest_feature_empty_list(self):
        """Test resolve_nearest_feature with empty feature list."""
        from sanitizer import resolve_nearest_feature
        
        selected_point = {"x": 0, "y": 0, "z": 0}
        features = []
        
        nearest = resolve_nearest_feature(selected_point, features)
        assert nearest is None


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.sanitizer = PlanSanitizer()
    
    def test_malformed_plan_structure(self):
        """Test handling of completely malformed plan."""
        plan = "not a dictionary"
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert len(messages) > 0
    
    def test_none_plan(self):
        """Test handling of None plan."""
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(None)
        
        assert is_valid is False
        assert len(messages) > 0
    
    def test_operation_with_missing_params(self):
        """Test operation with missing params field."""
        plan = {
            "plan_id": "test_016",
            "metadata": {
                "natural_language_prompt": "Missing params test"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch"
                    # Missing params field
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = self.sanitizer.sanitize_plan(plan)
        
        assert is_valid is False
        assert any("Missing required field: params" in msg for msg in messages)


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
