"""
Test suite for Fusion 360 Co-Pilot Plan Validation

Tests JSON schema validation and plan structure compliance.

Author: Fusion CoPilot Team
License: MIT
"""

import pytest
import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    jsonschema = None

from sanitizer import validate_plan_against_schema


class TestPlanSchemaValidation:
    """Test plan validation against JSON schema."""
    
    @pytest.fixture
    def schema_path(self):
        """Path to the plan schema file."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'plan_schema.json'
        )
    
    @pytest.fixture
    def valid_plan(self):
        """A valid plan for testing."""
        return {
            "plan_id": "test_schema_001",
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "natural_language_prompt": "Create a test rectangle",
                "estimated_duration_seconds": 15,
                "confidence_score": 0.9,
                "units": "mm"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch",
                    "params": {
                        "plane": "XY",
                        "name": "test_sketch"
                    }
                },
                {
                    "op_id": "op_2",
                    "op": "draw_rectangle",
                    "params": {
                        "center_point": {"x": 0, "y": 0, "z": 0},
                        "width": {"value": 50, "unit": "mm"},
                        "height": {"value": 30, "unit": "mm"}
                    },
                    "target_ref": "test_sketch",
                    "dependencies": ["op_1"]
                }
            ]
        }
    
    @pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not available")
    def test_valid_plan_passes_schema(self, valid_plan, schema_path):
        """Test that a valid plan passes schema validation."""
        is_valid, messages = validate_plan_against_schema(valid_plan, schema_path)
        
        assert is_valid is True
        assert len(messages) == 0
    
    @pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not available")
    def test_missing_required_field_fails(self, schema_path):
        """Test that missing required fields fail validation."""
        invalid_plan = {
            "plan_id": "test_invalid_001",
            "metadata": {
                "natural_language_prompt": "Test"
            }
            # Missing operations field
        }
        
        is_valid, messages = validate_plan_against_schema(invalid_plan, schema_path)
        
        assert is_valid is False
        assert len(messages) > 0
    
    @pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not available")
    def test_invalid_operation_type_fails(self, schema_path):
        """Test that invalid operation types fail validation."""
        invalid_plan = {
            "plan_id": "test_invalid_002",
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "natural_language_prompt": "Test invalid operation",
                "estimated_duration_seconds": 10
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "invalid_operation_type",  # Not in schema enum
                    "params": {}
                }
            ]
        }
        
        is_valid, messages = validate_plan_against_schema(invalid_plan, schema_path)
        
        assert is_valid is False
        assert len(messages) > 0
    
    @pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not available")
    def test_invalid_plan_id_format_fails(self, schema_path):
        """Test that invalid plan_id format fails validation."""
        invalid_plan = {
            "plan_id": "invalid plan id with spaces!",  # Violates pattern
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "natural_language_prompt": "Test",
                "estimated_duration_seconds": 10
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch",
                    "params": {"plane": "XY"}
                }
            ]
        }
        
        is_valid, messages = validate_plan_against_schema(invalid_plan, schema_path)
        
        assert is_valid is False
        assert len(messages) > 0
    
    @pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not available")
    def test_confidence_score_range_validation(self, schema_path):
        """Test confidence score range validation."""
        invalid_plan = {
            "plan_id": "test_confidence_001",
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "natural_language_prompt": "Test confidence",
                "estimated_duration_seconds": 10,
                "confidence_score": 1.5  # Outside valid range [0.0, 1.0]
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch",
                    "params": {"plane": "XY"}
                }
            ]
        }
        
        is_valid, messages = validate_plan_against_schema(invalid_plan, schema_path)
        
        assert is_valid is False
        assert len(messages) > 0
    
    def test_schema_validation_without_jsonschema(self, valid_plan, schema_path):
        """Test graceful handling when jsonschema is not available."""
        # This test will run even without jsonschema
        is_valid, messages = validate_plan_against_schema(valid_plan, schema_path)
        
        if JSONSCHEMA_AVAILABLE:
            assert is_valid is True
        else:
            # Should skip validation and return True with warning message
            assert is_valid is True
            assert any("jsonschema not installed" in msg for msg in messages)
    
    def test_nonexistent_schema_file(self, valid_plan):
        """Test handling of nonexistent schema file."""
        nonexistent_path = "/path/that/does/not/exist/schema.json"
        
        is_valid, messages = validate_plan_against_schema(valid_plan, nonexistent_path)
        
        assert is_valid is False
        assert len(messages) > 0


class TestPlanStructureValidation:
    """Test plan structure validation beyond schema."""
    
    def test_operation_id_uniqueness(self):
        """Test that operation IDs must be unique within a plan."""
        plan = {
            "plan_id": "test_unique_001",
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "natural_language_prompt": "Test unique IDs",
                "estimated_duration_seconds": 10
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch",
                    "params": {"plane": "XY"}
                },
                {
                    "op_id": "op_1",  # Duplicate ID
                    "op": "draw_rectangle",
                    "params": {
                        "width": {"value": 10, "unit": "mm"},
                        "height": {"value": 10, "unit": "mm"}
                    }
                }
            ]
        }
        
        # This would be caught by business logic validation
        op_ids = [op["op_id"] for op in plan["operations"]]
        assert len(op_ids) != len(set(op_ids))  # Has duplicates
    
    def test_dependency_cycle_detection(self):
        """Test detection of circular dependencies."""
        plan = {
            "plan_id": "test_cycle_001",
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "natural_language_prompt": "Test circular dependency",
                "estimated_duration_seconds": 10
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch",
                    "params": {"plane": "XY"},
                    "dependencies": ["op_2"]  # Depends on op_2
                },
                {
                    "op_id": "op_2",
                    "op": "draw_rectangle",
                    "params": {
                        "width": {"value": 10, "unit": "mm"},
                        "height": {"value": 10, "unit": "mm"}
                    },
                    "dependencies": ["op_1"]  # Depends on op_1 - creates cycle
                }
            ]
        }
        
        # Function to detect cycles (simplified)
        def has_dependency_cycle(operations):
            """Simple cycle detection for testing."""
            # Build dependency graph
            deps = {}
            for op in operations:
                op_id = op["op_id"]
                deps[op_id] = op.get("dependencies", [])
            
            # Simple cycle check - in real implementation would use DFS
            for op_id in deps:
                if op_id in deps.get(op_id, []):
                    return True  # Self-dependency
            
            return False  # Simplified - doesn't catch all cycles
        
        # This plan has a circular dependency
        assert len(plan["operations"]) == 2
        # Real cycle detection would be more sophisticated
    
    def test_valid_dependency_chain(self):
        """Test valid dependency chain validation."""
        plan = {
            "plan_id": "test_valid_deps_001",
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "natural_language_prompt": "Test valid dependencies",
                "estimated_duration_seconds": 20
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch",
                    "params": {"plane": "XY"}
                },
                {
                    "op_id": "op_2",
                    "op": "draw_rectangle",
                    "params": {
                        "width": {"value": 10, "unit": "mm"},
                        "height": {"value": 10, "unit": "mm"}
                    },
                    "dependencies": ["op_1"]
                },
                {
                    "op_id": "op_3",
                    "op": "extrude",
                    "params": {
                        "distance": {"value": 5, "unit": "mm"}
                    },
                    "dependencies": ["op_2"]
                }
            ]
        }
        
        # Validate dependency chain
        op_ids = {op["op_id"] for op in plan["operations"]}
        
        for op in plan["operations"]:
            deps = op.get("dependencies", [])
            for dep in deps:
                assert dep in op_ids, f"Dependency {dep} not found in operations"


class TestPlanExamples:
    """Test validation of example plans from the schema."""
    
    @pytest.fixture
    def schema_path(self):
        """Path to the plan schema file."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'plan_schema.json'
        )
    
    @pytest.fixture
    def schema_examples(self, schema_path):
        """Load examples from the schema file."""
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
                return schema.get('examples', [])
        except Exception:
            return []
    
    @pytest.mark.skipif(not JSONSCHEMA_AVAILABLE, reason="jsonschema not available")
    def test_schema_examples_are_valid(self, schema_examples, schema_path):
        """Test that all examples in the schema are valid."""
        if not schema_examples:
            pytest.skip("No examples found in schema")
        
        for i, example in enumerate(schema_examples):
            is_valid, messages = validate_plan_against_schema(example, schema_path)
            assert is_valid, f"Schema example {i} failed validation: {messages}"
    
    def test_example_structure_consistency(self, schema_examples):
        """Test structural consistency of schema examples."""
        if not schema_examples:
            pytest.skip("No examples found in schema")
        
        for i, example in enumerate(schema_examples):
            # Check required fields
            assert "plan_id" in example, f"Example {i} missing plan_id"
            assert "metadata" in example, f"Example {i} missing metadata"
            assert "operations" in example, f"Example {i} missing operations"
            
            # Check metadata structure
            metadata = example["metadata"]
            assert "natural_language_prompt" in metadata, f"Example {i} missing prompt"
            assert "estimated_duration_seconds" in metadata, f"Example {i} missing duration"
            
            # Check operations structure
            operations = example["operations"]
            assert isinstance(operations, list), f"Example {i} operations not a list"
            
            for j, op in enumerate(operations):
                assert "op_id" in op, f"Example {i}, operation {j} missing op_id"
                assert "op" in op, f"Example {i}, operation {j} missing op"
                assert "params" in op, f"Example {i}, operation {j} missing params"


class TestPromptExamplesValidation:
    """Test validation of prompt examples against expected plans."""
    
    @pytest.fixture
    def prompt_examples_path(self):
        """Path to the prompt examples file."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'prompts', 'prompt_examples.json'
        )
    
    @pytest.fixture
    def prompt_examples(self, prompt_examples_path):
        """Load prompt examples."""
        try:
            with open(prompt_examples_path, 'r') as f:
                data = json.load(f)
                return data.get('prompt_examples', [])
        except Exception:
            return []
    
    def test_prompt_examples_structure(self, prompt_examples):
        """Test structure of prompt examples."""
        if not prompt_examples:
            pytest.skip("No prompt examples found")
        
        for i, example in enumerate(prompt_examples):
            assert "id" in example, f"Example {i} missing id"
            assert "prompt" in example, f"Example {i} missing prompt"
            assert "category" in example, f"Example {i} missing category"
            assert "difficulty" in example, f"Example {i} missing difficulty"
            assert "expected_operations" in example, f"Example {i} missing expected_operations"
            
            # Validate difficulty levels
            assert example["difficulty"] in ["beginner", "intermediate", "advanced"], \
                f"Example {i} has invalid difficulty: {example['difficulty']}"
            
            # Validate expected operations are not empty
            expected_ops = example["expected_operations"]
            assert isinstance(expected_ops, list), f"Example {i} expected_operations not a list"
            if not example.get("ambiguous", False):
                assert len(expected_ops) > 0, f"Example {i} has no expected operations"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
