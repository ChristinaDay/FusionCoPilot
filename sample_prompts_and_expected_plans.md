# Fusion 360 Co-Pilot - Sample Prompts and Expected Plans

This document provides comprehensive examples of natural language prompts and their corresponding structured plans. These examples serve as:

- **Training data** for understanding system capabilities
- **Test cases** for validation and regression testing  
- **User guidance** for effective prompt construction
- **Development reference** for extending functionality

## How to Use This Document

Each example includes:
- **Natural Language Prompt**: What the user would type
- **Expected Plan Structure**: JSON representation of operations
- **Complexity Level**: Beginner, Intermediate, or Advanced
- **Notes**: Special considerations, ambiguity handling, or prerequisites

---

## Basic Geometric Shapes

### 1. Simple Rectangular Plate

**Prompt**: `"Create a 100x50mm rectangular plate that's 5mm thick"`

**Expected Plan**:
```json
{
  "plan_id": "simple_plate_001",
  "metadata": {
    "natural_language_prompt": "Create a 100x50mm rectangular plate that's 5mm thick",
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
    },
    {
      "op_id": "op_3",
      "op": "extrude",
      "params": {
        "profile": "base_sketch",
        "distance": {"value": 5, "unit": "mm"},
        "direction": "positive",
        "operation": "new_body"
      },
      "dependencies": ["op_2"]
    }
  ]
}
```

**Complexity**: Beginner  
**Notes**: Basic extrusion workflow, clear dimensions, no ambiguity

---

### 2. Unit Cube

**Prompt**: `"Make a cube that's 25mm on all sides"`

**Expected Plan**:
```json
{
  "plan_id": "unit_cube_001",
  "metadata": {
    "natural_language_prompt": "Make a cube that's 25mm on all sides",
    "estimated_duration_seconds": 12,
    "confidence_score": 0.92,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_sketch",
      "params": {
        "plane": "XY",
        "name": "cube_base"
      }
    },
    {
      "op_id": "op_2",
      "op": "draw_rectangle",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "width": {"value": 25, "unit": "mm"},
        "height": {"value": 25, "unit": "mm"}
      },
      "target_ref": "cube_base",
      "dependencies": ["op_1"]
    },
    {
      "op_id": "op_3",
      "op": "extrude",
      "params": {
        "profile": "cube_base",
        "distance": {"value": 25, "unit": "mm"},
        "direction": "positive",
        "operation": "new_body"
      },
      "dependencies": ["op_2"]
    }
  ]
}
```

**Complexity**: Beginner  
**Notes**: Equal dimensions inferred from "cube", square base assumed

---

### 3. Cylinder

**Prompt**: `"Create a cylinder 20mm diameter and 30mm tall"`

**Expected Plan**:
```json
{
  "plan_id": "cylinder_001",
  "metadata": {
    "natural_language_prompt": "Create a cylinder 20mm diameter and 30mm tall",
    "estimated_duration_seconds": 18,
    "confidence_score": 0.90,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_sketch",
      "params": {
        "plane": "XY",
        "name": "circle_sketch"
      }
    },
    {
      "op_id": "op_2",
      "op": "draw_circle",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "diameter": {"value": 20, "unit": "mm"}
      },
      "target_ref": "circle_sketch",
      "dependencies": ["op_1"]
    },
    {
      "op_id": "op_3",
      "op": "extrude",
      "params": {
        "profile": "circle_sketch",
        "distance": {"value": 30, "unit": "mm"},
        "direction": "positive",
        "operation": "new_body"
      },
      "dependencies": ["op_2"]
    }
  ]
}
```

**Complexity**: Beginner  
**Notes**: "Tall" interpreted as height/extrusion distance

---

## Holes and Features

### 4. Center Hole

**Prompt**: `"Add a 6mm hole in the center of this face"`

**Expected Plan**:
```json
{
  "plan_id": "center_hole_001",
  "metadata": {
    "natural_language_prompt": "Add a 6mm hole in the center of this face",
    "estimated_duration_seconds": 10,
    "confidence_score": 0.88,
    "units": "mm",
    "requires_user_input": false
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_hole",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "diameter": {"value": 6, "unit": "mm"},
        "depth": "through_all",
        "hole_type": "simple"
      },
      "target_ref": "face_selected"
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: Assumes user has pre-selected a face, center point calculated relative to face bounds

---

### 5. Corner Holes Pattern

**Prompt**: `"Create 4 corner holes, 8mm diameter, 10mm from edges"`

**Expected Plan**:
```json
{
  "plan_id": "corner_holes_001",
  "metadata": {
    "natural_language_prompt": "Create 4 corner holes, 8mm diameter, 10mm from edges",
    "estimated_duration_seconds": 25,
    "confidence_score": 0.85,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_hole",
      "params": {
        "center_point": {"x": 40, "y": 20, "z": 0},
        "diameter": {"value": 8, "unit": "mm"},
        "depth": "through_all",
        "hole_type": "simple"
      },
      "target_ref": "face_top"
    },
    {
      "op_id": "op_2",
      "op": "pattern_rectangular",
      "params": {
        "feature_to_pattern": "op_1",
        "direction_1": {"x": 1, "y": 0, "z": 0},
        "direction_2": {"x": 0, "y": 1, "z": 0},
        "distance_1": {"value": 80, "unit": "mm"},
        "distance_2": {"value": 40, "unit": "mm"},
        "count_1": 2,
        "count_2": 2
      },
      "dependencies": ["op_1"]
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: Pattern inferred from "4 corner holes", distances calculated from edge offset

---

### 6. Countersunk Hole

**Prompt**: `"Make a countersunk hole 6mm diameter with 12mm countersink"`

**Expected Plan**:
```json
{
  "plan_id": "countersunk_hole_001",
  "metadata": {
    "natural_language_prompt": "Make a countersunk hole 6mm diameter with 12mm countersink",
    "estimated_duration_seconds": 18,
    "confidence_score": 0.82,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "countersink_hole",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "hole_diameter": {"value": 6, "unit": "mm"},
        "countersink_diameter": {"value": 12, "unit": "mm"},
        "countersink_angle": {"value": 90, "unit": "deg"},
        "depth": "through_all"
      },
      "target_ref": "face_selected"
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: Standard 90° countersink angle assumed, requires specialized hole operation

---

## Edge Modifications

### 7. Fillet All Edges

**Prompt**: `"Fillet all edges with 3mm radius"`

**Expected Plan**:
```json
{
  "plan_id": "fillet_all_001",
  "metadata": {
    "natural_language_prompt": "Fillet all edges with 3mm radius",
    "estimated_duration_seconds": 20,
    "confidence_score": 0.82,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "fillet",
      "params": {
        "radius": {"value": 3, "unit": "mm"},
        "edges": "all_edges",
        "fillet_type": "constant_radius"
      }
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: "All edges" requires edge detection and selection, may need validation for feasibility

---

### 8. Chamfer Top Edges

**Prompt**: `"Chamfer the top edges by 2mm at 45 degrees"`

**Expected Plan**:
```json
{
  "plan_id": "chamfer_top_001",
  "metadata": {
    "natural_language_prompt": "Chamfer the top edges by 2mm at 45 degrees",
    "estimated_duration_seconds": 18,
    "confidence_score": 0.83,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "chamfer",
      "params": {
        "distance": {"value": 2, "unit": "mm"},
        "angle": {"value": 45, "unit": "deg"},
        "edges": "top_edges",
        "chamfer_type": "distance_angle"
      }
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: "Top edges" requires geometric analysis to identify correct edges

---

## Patterns

### 9. Linear Hole Pattern

**Prompt**: `"Create a linear pattern of 5 holes spaced 20mm apart along the X-axis"`

**Expected Plan**:
```json
{
  "plan_id": "linear_pattern_001",
  "metadata": {
    "natural_language_prompt": "Create a linear pattern of 5 holes spaced 20mm apart along the X-axis",
    "estimated_duration_seconds": 22,
    "confidence_score": 0.88,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_hole",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "diameter": {"value": 5, "unit": "mm"},
        "depth": "through_all",
        "hole_type": "simple"
      },
      "target_ref": "face_selected"
    },
    {
      "op_id": "op_2",
      "op": "pattern_linear",
      "params": {
        "feature_to_pattern": "op_1",
        "direction": {"x": 1, "y": 0, "z": 0},
        "distance": {"value": 20, "unit": "mm"},
        "count": 5
      },
      "dependencies": ["op_1"]
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: Default hole diameter assumed (5mm), X-axis direction clearly specified

---

### 10. Circular Pattern

**Prompt**: `"Make a circular pattern of 8 holes around the center, 40mm radius"`

**Expected Plan**:
```json
{
  "plan_id": "circular_pattern_001",
  "metadata": {
    "natural_language_prompt": "Make a circular pattern of 8 holes around the center, 40mm radius",
    "estimated_duration_seconds": 28,
    "confidence_score": 0.85,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_hole",
      "params": {
        "center_point": {"x": 40, "y": 0, "z": 0},
        "diameter": {"value": 4, "unit": "mm"},
        "depth": "through_all",
        "hole_type": "simple"
      },
      "target_ref": "face_selected"
    },
    {
      "op_id": "op_2",
      "op": "pattern_circular",
      "params": {
        "feature_to_pattern": "op_1",
        "center_point": {"x": 0, "y": 0, "z": 0},
        "axis": {"x": 0, "y": 0, "z": 1},
        "count": 8,
        "angle": {"value": 360, "unit": "deg"}
      },
      "dependencies": ["op_1"]
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: First hole positioned at pattern radius, center point assumed at origin

---

## Advanced Operations

### 11. Shell Operation

**Prompt**: `"Shell this part with 2mm wall thickness, remove the top face"`

**Expected Plan**:
```json
{
  "plan_id": "shell_001",
  "metadata": {
    "natural_language_prompt": "Shell this part with 2mm wall thickness, remove the top face",
    "estimated_duration_seconds": 35,
    "confidence_score": 0.75,
    "units": "mm",
    "requires_user_input": false
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "shell",
      "params": {
        "thickness": {"value": 2, "unit": "mm"},
        "faces_to_remove": ["face_top"],
        "shell_type": "outward"
      }
    }
  ]
}
```

**Complexity**: Advanced  
**Notes**: Requires face identification, shell direction assumed as outward

---

### 12. Mirror Feature

**Prompt**: `"Mirror this feature across the YZ plane"`

**Expected Plan**:
```json
{
  "plan_id": "mirror_001",
  "metadata": {
    "natural_language_prompt": "Mirror this feature across the YZ plane",
    "estimated_duration_seconds": 15,
    "confidence_score": 0.78,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "mirror",
      "params": {
        "features_to_mirror": ["feature_selected"],
        "mirror_plane": "YZ",
        "plane_origin": {"x": 0, "y": 0, "z": 0}
      }
    }
  ]
}
```

**Complexity**: Advanced  
**Notes**: Assumes user has selected feature to mirror, standard plane reference

---

### 13. Construction Plane

**Prompt**: `"Create a construction plane 25mm offset from the XY plane"`

**Expected Plan**:
```json
{
  "plan_id": "construction_plane_001",
  "metadata": {
    "natural_language_prompt": "Create a construction plane 25mm offset from the XY plane",
    "estimated_duration_seconds": 12,
    "confidence_score": 0.90,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_plane",
      "params": {
        "plane_type": "offset",
        "reference_plane": "XY",
        "offset_distance": {"value": 25, "unit": "mm"},
        "offset_direction": "positive"
      }
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: Construction geometry, positive direction assumed (upward for XY plane)

---

## Complex Multi-Step Operations

### 14. Hexagonal Prism

**Prompt**: `"Create a hexagonal prism 30mm across flats, 15mm tall"`

**Expected Plan**:
```json
{
  "plan_id": "hexagon_001",
  "metadata": {
    "natural_language_prompt": "Create a hexagonal prism 30mm across flats, 15mm tall",
    "estimated_duration_seconds": 25,
    "confidence_score": 0.82,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_sketch",
      "params": {
        "plane": "XY",
        "name": "hex_sketch"
      }
    },
    {
      "op_id": "op_2",
      "op": "draw_polygon",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "sides": 6,
        "size_type": "across_flats",
        "size": {"value": 30, "unit": "mm"}
      },
      "target_ref": "hex_sketch",
      "dependencies": ["op_1"]
    },
    {
      "op_id": "op_3",
      "op": "extrude",
      "params": {
        "profile": "hex_sketch",
        "distance": {"value": 15, "unit": "mm"},
        "direction": "positive",
        "operation": "new_body"
      },
      "dependencies": ["op_2"]
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: "Across flats" vs "across corners" specification important for hexagons

---

### 15. Complex Mounting Plate

**Prompt**: `"Create a mounting plate: 80x60x8mm with 4 corner holes (6mm) and a center cutout (20x30mm)"`

**Expected Plan**:
```json
{
  "plan_id": "mounting_plate_001",
  "metadata": {
    "natural_language_prompt": "Create a mounting plate: 80x60x8mm with 4 corner holes (6mm) and a center cutout (20x30mm)",
    "estimated_duration_seconds": 45,
    "confidence_score": 0.88,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_sketch",
      "params": {
        "plane": "XY",
        "name": "base_plate"
      }
    },
    {
      "op_id": "op_2",
      "op": "draw_rectangle",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "width": {"value": 80, "unit": "mm"},
        "height": {"value": 60, "unit": "mm"}
      },
      "target_ref": "base_plate",
      "dependencies": ["op_1"]
    },
    {
      "op_id": "op_3",
      "op": "extrude",
      "params": {
        "profile": "base_plate",
        "distance": {"value": 8, "unit": "mm"},
        "direction": "positive",
        "operation": "new_body"
      },
      "dependencies": ["op_2"]
    },
    {
      "op_id": "op_4",
      "op": "create_sketch",
      "params": {
        "plane": "face_top",
        "name": "cutout_sketch"
      },
      "dependencies": ["op_3"]
    },
    {
      "op_id": "op_5",
      "op": "draw_rectangle",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "width": {"value": 20, "unit": "mm"},
        "height": {"value": 30, "unit": "mm"}
      },
      "target_ref": "cutout_sketch",
      "dependencies": ["op_4"]
    },
    {
      "op_id": "op_6",
      "op": "cut",
      "params": {
        "profile": "cutout_sketch",
        "distance": {"value": 8, "unit": "mm"},
        "direction": "negative",
        "operation": "cut"
      },
      "dependencies": ["op_5"]
    },
    {
      "op_id": "op_7",
      "op": "create_hole",
      "params": {
        "center_point": {"x": 30, "y": 20, "z": 0},
        "diameter": {"value": 6, "unit": "mm"},
        "depth": "through_all",
        "hole_type": "simple"
      },
      "target_ref": "face_top",
      "dependencies": ["op_6"]
    },
    {
      "op_id": "op_8",
      "op": "pattern_rectangular",
      "params": {
        "feature_to_pattern": "op_7",
        "direction_1": {"x": 1, "y": 0, "z": 0},
        "direction_2": {"x": 0, "y": 1, "z": 0},
        "distance_1": {"value": 60, "unit": "mm"},
        "distance_2": {"value": 40, "unit": "mm"},
        "count_1": 2,
        "count_2": 2
      },
      "dependencies": ["op_7"]
    }
  ]
}
```

**Complexity**: Advanced  
**Notes**: Multi-step operation requiring careful sequencing, hole positioning calculated for corners

---

## Ambiguous Requests & Clarification

### 16. Ambiguous Size Reference

**Prompt**: `"Make the top-left hole 2mm larger in diameter"`

**Expected Plan**:
```json
{
  "plan_id": "ambiguous_hole_001",
  "metadata": {
    "natural_language_prompt": "Make the top-left hole 2mm larger in diameter",
    "estimated_duration_seconds": 15,
    "confidence_score": 0.45,
    "units": "mm",
    "requires_user_input": true,
    "clarification_questions": [
      "Which hole is the 'top-left' hole? Please select the hole or provide coordinates.",
      "What is the current diameter of the hole to be modified?"
    ]
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "set_dimension",
      "params": {
        "feature_ref": "hole_top_left",
        "dimension_type": "diameter",
        "new_value": {"value": "current_value + 2", "unit": "mm"}
      }
    }
  ]
}
```

**Complexity**: Advanced  
**Notes**: Requires clarification, demonstrates ambiguity handling

---

### 17. Vague Request

**Prompt**: `"Make it bigger"`

**Expected Plan**:
```json
{
  "plan_id": "vague_request_001",
  "metadata": {
    "natural_language_prompt": "Make it bigger",
    "estimated_duration_seconds": 0,
    "confidence_score": 0.10,
    "units": "mm",
    "requires_user_input": true,
    "clarification_questions": [
      "What would you like to make bigger? Please specify the feature or dimension.",
      "By how much would you like to increase the size?",
      "Which dimension should be changed (length, width, height, diameter, etc.)?"
    ]
  },
  "operations": []
}
```

**Complexity**: Beginner  
**Notes**: Example of insufficient information requiring clarification

---

## Unit Conversion Examples

### 18. Mixed Units

**Prompt**: `"Create a 4 inch by 2 inch plate that's 5mm thick"`

**Expected Plan**:
```json
{
  "plan_id": "mixed_units_001",
  "metadata": {
    "natural_language_prompt": "Create a 4 inch by 2 inch plate that's 5mm thick",
    "estimated_duration_seconds": 18,
    "confidence_score": 0.90,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_sketch",
      "params": {
        "plane": "XY",
        "name": "mixed_units_sketch"
      }
    },
    {
      "op_id": "op_2",
      "op": "draw_rectangle",
      "params": {
        "center_point": {"x": 0, "y": 0, "z": 0},
        "width": {"value": 101.6, "unit": "mm", "original_value": 4, "original_unit": "in"},
        "height": {"value": 50.8, "unit": "mm", "original_value": 2, "original_unit": "in"}
      },
      "target_ref": "mixed_units_sketch",
      "dependencies": ["op_1"]
    },
    {
      "op_id": "op_3",
      "op": "extrude",
      "params": {
        "profile": "mixed_units_sketch",
        "distance": {"value": 5, "unit": "mm"},
        "direction": "positive",
        "operation": "new_body"
      },
      "dependencies": ["op_2"]
    }
  ]
}
```

**Complexity**: Intermediate  
**Notes**: Demonstrates unit conversion, original values preserved for reference

---

## Advanced Geometric Operations

### 19. Revolve Operation

**Prompt**: `"Revolve this profile 270 degrees around the Y-axis"`

**Expected Plan**:
```json
{
  "plan_id": "revolve_001",
  "metadata": {
    "natural_language_prompt": "Revolve this profile 270 degrees around the Y-axis",
    "estimated_duration_seconds": 25,
    "confidence_score": 0.85,
    "units": "deg"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "revolve",
      "params": {
        "profile": "sketch_selected",
        "axis_line": {"point1": {"x": 0, "y": 0, "z": 0}, "point2": {"x": 0, "y": 1, "z": 0}},
        "angle": {"value": 270, "unit": "deg"},
        "operation": "new_body"
      }
    }
  ]
}
```

**Complexity**: Advanced  
**Notes**: Requires pre-selected sketch profile, partial revolution specified

---

### 20. Component Creation

**Prompt**: `"Create a new component for the mounting bracket"`

**Expected Plan**:
```json
{
  "plan_id": "component_001",
  "metadata": {
    "natural_language_prompt": "Create a new component for the mounting bracket",
    "estimated_duration_seconds": 8,
    "confidence_score": 0.92,
    "units": "mm"
  },
  "operations": [
    {
      "op_id": "op_1",
      "op": "create_component",
      "params": {
        "component_name": "mounting_bracket",
        "activate_component": true,
        "insert_point": {"x": 0, "y": 0, "z": 0}
      }
    }
  ]
}
```

**Complexity**: Advanced  
**Notes**: Assembly-level operation, component name extracted from prompt

---

## Testing and Validation Guidelines

### Prompt Quality Criteria

**High-Quality Prompts**:
- Clear dimensional specifications
- Unambiguous geometric references  
- Logical operation sequences
- Standard CAD terminology

**Challenging Prompts**:
- Multiple interpretations possible
- Missing critical information
- Complex multi-step operations
- Non-standard terminology

### Expected Behavior

**Successful Parsing**:
- Confidence score > 0.7
- All required parameters present
- Logical operation dependencies
- Reasonable execution time estimates

**Clarification Required**:
- Confidence score < 0.5
- Missing critical dimensions
- Ambiguous feature references
- Multiple valid interpretations

**Error Handling**:
- Invalid operations for current context
- Impossible geometric constraints
- Missing prerequisite features
- Unit conversion failures

### Test Automation

These examples can be used for:

1. **Regression Testing**: Ensure consistent parsing results
2. **Performance Testing**: Validate response times
3. **Accuracy Testing**: Compare generated vs expected plans
4. **Edge Case Testing**: Handle ambiguous or invalid inputs
5. **Integration Testing**: End-to-end workflow validation

---

## Usage Notes

### For Developers

- Use these examples as training data for LLM fine-tuning
- Implement plan validation against these expected structures
- Test edge cases and error conditions
- Benchmark parsing performance and accuracy

### For Users

- Study successful prompt patterns
- Understand how ambiguity affects results
- Learn to provide clear dimensional specifications
- Practice with increasing complexity levels

### For QA Testing

- Verify each example produces expected results
- Test variations and edge cases
- Validate error handling and clarification flows
- Ensure consistent behavior across updates

---

*This document is maintained as part of the Fusion 360 Co-Pilot development pack and should be updated as new capabilities are added or existing behavior is modified.*
