#!/usr/bin/env python3
"""
Fusion 360 Co-Pilot - Test Fixture Generator

Generates test fixtures and placeholder files for development and testing.
Since we can't generate actual STEP/STL files without CAD libraries,
this script creates instructions and JSON metadata for test scenarios.

Usage:
    python generate_test_fixtures.py [--output-dir fixtures] [--format json|instructions]

Author: Fusion CoPilot Team
License: MIT
"""

import json
import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def create_fixture_metadata(name: str, description: str, geometry_type: str, 
                          dimensions: Dict, units: str = "mm") -> Dict:
    """Create metadata for a test fixture."""
    return {
        "name": name,
        "description": description,
        "geometry_type": geometry_type,
        "dimensions": dimensions,
        "units": units,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "format": "metadata_only",
        "usage": "testing",
        "complexity": classify_complexity(geometry_type, dimensions)
    }


def classify_complexity(geometry_type: str, dimensions: Dict) -> str:
    """Classify fixture complexity based on geometry and dimensions."""
    if geometry_type in ["rectangle", "circle", "cube"]:
        return "simple"
    elif geometry_type in ["cylinder", "hexagon", "pattern"]:
        return "intermediate"
    else:
        return "complex"


def generate_basic_fixtures() -> List[Dict]:
    """Generate basic geometric test fixtures."""
    fixtures = []
    
    # Simple rectangle plate
    fixtures.append(create_fixture_metadata(
        "simple_plate",
        "Basic rectangular plate for extrusion testing",
        "rectangle",
        {"width": 100, "height": 50, "thickness": 5}
    ))
    
    # Square cube
    fixtures.append(create_fixture_metadata(
        "unit_cube", 
        "25mm cube for basic operations testing",
        "cube",
        {"width": 25, "height": 25, "depth": 25}
    ))
    
    # Circular disk
    fixtures.append(create_fixture_metadata(
        "circular_disk",
        "Circular disk for hole and pattern testing",
        "circle",
        {"diameter": 60, "thickness": 8}
    ))
    
    # Cylinder
    fixtures.append(create_fixture_metadata(
        "test_cylinder",
        "Cylindrical part for revolve and cut testing", 
        "cylinder",
        {"diameter": 30, "height": 40}
    ))
    
    # Hexagonal prism
    fixtures.append(create_fixture_metadata(
        "hex_prism",
        "Hexagonal prism for polygon testing",
        "hexagon", 
        {"across_flats": 20, "height": 15}
    ))
    
    return fixtures


def generate_complex_fixtures() -> List[Dict]:
    """Generate complex test fixtures with multiple features."""
    fixtures = []
    
    # Mounting plate with holes
    fixtures.append({
        "name": "mounting_plate_4holes",
        "description": "Mounting plate with 4 corner holes for pattern testing",
        "geometry_type": "complex",
        "features": [
            {
                "type": "rectangle",
                "dimensions": {"width": 80, "height": 60, "thickness": 8}
            },
            {
                "type": "hole_pattern",
                "pattern_type": "rectangular",
                "hole_diameter": 6,
                "spacing": {"x": 60, "y": 40},
                "count": {"x": 2, "y": 2}
            }
        ],
        "units": "mm",
        "complexity": "intermediate",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    
    # Part with cutout
    fixtures.append({
        "name": "plate_with_cutout",
        "description": "Plate with rectangular cutout for cut operation testing",
        "geometry_type": "complex",
        "features": [
            {
                "type": "rectangle", 
                "dimensions": {"width": 100, "height": 60, "thickness": 10}
            },
            {
                "type": "cutout",
                "shape": "rectangle",
                "dimensions": {"width": 30, "height": 20},
                "position": {"x": 0, "y": 0}  # Center
            }
        ],
        "units": "mm",
        "complexity": "intermediate",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    
    # Filleted part
    fixtures.append({
        "name": "filleted_block",
        "description": "Block with filleted edges for edge modification testing",
        "geometry_type": "complex",
        "features": [
            {
                "type": "rectangle",
                "dimensions": {"width": 40, "height": 30, "thickness": 20}
            },
            {
                "type": "fillet",
                "radius": 3,
                "edges": "all"
            }
        ],
        "units": "mm", 
        "complexity": "intermediate",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    
    return fixtures


def generate_assembly_fixtures() -> List[Dict]:
    """Generate assembly test fixtures."""
    fixtures = []
    
    # Simple two-part assembly
    fixtures.append({
        "name": "simple_assembly",
        "description": "Two-part assembly for component testing",
        "geometry_type": "assembly",
        "components": [
            {
                "name": "base_plate",
                "type": "rectangle",
                "dimensions": {"width": 80, "height": 60, "thickness": 10},
                "position": {"x": 0, "y": 0, "z": 0}
            },
            {
                "name": "mounting_block", 
                "type": "cube",
                "dimensions": {"width": 20, "height": 20, "depth": 15},
                "position": {"x": 0, "y": 0, "z": 10}
            }
        ],
        "units": "mm",
        "complexity": "advanced",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    
    return fixtures


def generate_step_file_instructions() -> str:
    """Generate instructions for creating STEP files manually."""
    return """
# STEP File Creation Instructions

Since this development environment cannot generate actual STEP files, 
follow these instructions to create test fixtures manually in Fusion 360:

## Basic Fixtures

### 1. Simple Plate (simple_plate.step)
1. Create new design
2. Create sketch on XY plane
3. Draw rectangle: 100mm x 50mm, centered at origin
4. Extrude: 5mm upward
5. Export as STEP: simple_plate.step

### 2. Unit Cube (unit_cube.step)  
1. Create new design
2. Create sketch on XY plane
3. Draw square: 25mm x 25mm, centered at origin
4. Extrude: 25mm upward
5. Export as STEP: unit_cube.step

### 3. Circular Disk (circular_disk.step)
1. Create new design
2. Create sketch on XY plane  
3. Draw circle: 60mm diameter, centered at origin
4. Extrude: 8mm upward
5. Export as STEP: circular_disk.step

### 4. Test Cylinder (test_cylinder.step)
1. Create new design
2. Create sketch on XY plane
3. Draw circle: 30mm diameter, centered at origin  
4. Extrude: 40mm upward
5. Export as STEP: test_cylinder.step

### 5. Hexagonal Prism (hex_prism.step)
1. Create new design
2. Create sketch on XY plane
3. Draw polygon: 6 sides, 20mm across flats, centered at origin
4. Extrude: 15mm upward  
5. Export as STEP: hex_prism.step

## Complex Fixtures

### 6. Mounting Plate with 4 Holes (mounting_plate_4holes.step)
1. Create new design
2. Create sketch on XY plane
3. Draw rectangle: 80mm x 60mm, centered at origin
4. Extrude: 8mm upward
5. Create holes: 6mm diameter at corners (±30mm, ±20mm from center)
6. Export as STEP: mounting_plate_4holes.step

### 7. Plate with Cutout (plate_with_cutout.step)
1. Create new design  
2. Create sketch on XY plane
3. Draw rectangle: 100mm x 60mm, centered at origin
4. Extrude: 10mm upward
5. Create sketch on top face
6. Draw rectangle: 30mm x 20mm, centered 
7. Cut extrude: through all
8. Export as STEP: plate_with_cutout.step

### 8. Filleted Block (filleted_block.step)
1. Create new design
2. Create sketch on XY plane  
3. Draw rectangle: 40mm x 30mm, centered at origin
4. Extrude: 20mm upward
5. Fillet all edges: 3mm radius
6. Export as STEP: filleted_block.step

## Usage in Testing

Place generated STEP files in the fixtures/ directory:
```
fixtures/
├── simple_plate.step
├── unit_cube.step  
├── circular_disk.step
├── test_cylinder.step
├── hex_prism.step
├── mounting_plate_4holes.step
├── plate_with_cutout.step
└── filleted_block.step
```

These files can then be imported into test scenarios to validate:
- Import/export functionality
- Geometry recognition
- Feature detection
- Dimension extraction
- Plan generation accuracy

## Automated Testing

For CI/CD pipelines where manual STEP file creation isn't feasible,
the JSON metadata files serve as lightweight substitutes that contain
all the geometric information needed for plan validation testing.
"""


def create_ci_test_data() -> Dict:
    """Create test data suitable for CI environments."""
    return {
        "test_scenarios": [
            {
                "name": "basic_extrusion",
                "input_prompt": "Create a 50x30mm plate that's 5mm thick",
                "expected_operations": ["create_sketch", "draw_rectangle", "extrude"],
                "expected_dimensions": {"width": 50, "height": 30, "thickness": 5},
                "complexity": "simple"
            },
            {
                "name": "hole_creation", 
                "input_prompt": "Add a 6mm hole in the center",
                "expected_operations": ["create_hole"],
                "expected_dimensions": {"diameter": 6},
                "complexity": "simple",
                "requires_existing_geometry": True
            },
            {
                "name": "pattern_creation",
                "input_prompt": "Create 4 holes in corners, 8mm diameter",
                "expected_operations": ["create_hole", "pattern_rectangular"],
                "expected_dimensions": {"hole_diameter": 8, "count": 4},
                "complexity": "intermediate"
            },
            {
                "name": "fillet_application",
                "input_prompt": "Fillet all edges with 3mm radius", 
                "expected_operations": ["fillet"],
                "expected_dimensions": {"radius": 3},
                "complexity": "intermediate",
                "requires_existing_geometry": True
            },
            {
                "name": "complex_part",
                "input_prompt": "Create mounting bracket: 80x60x8mm with center cutout 20x30mm and 4 corner holes 6mm",
                "expected_operations": ["create_sketch", "draw_rectangle", "extrude", "create_sketch", "draw_rectangle", "cut", "create_hole", "pattern_rectangular"],
                "complexity": "advanced"
            }
        ],
        "validation_rules": [
            {
                "rule": "positive_dimensions",
                "description": "All dimensions must be positive numbers"
            },
            {
                "rule": "reasonable_sizes", 
                "description": "Dimensions should be within reasonable manufacturing limits"
            },
            {
                "rule": "operation_sequence",
                "description": "Operations should follow logical CAD sequence"
            },
            {
                "rule": "dependency_satisfaction",
                "description": "All operation dependencies must be satisfied"
            }
        ]
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate test fixtures for Fusion 360 Co-Pilot")
    parser.add_argument("--output-dir", default="fixtures", help="Output directory for fixtures")
    parser.add_argument("--format", choices=["json", "instructions", "both"], default="both", 
                       help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if args.verbose:
        print(f"Generating test fixtures in: {output_dir}")
    
    # Generate fixture metadata
    if args.format in ["json", "both"]:
        all_fixtures = {
            "basic_fixtures": generate_basic_fixtures(),
            "complex_fixtures": generate_complex_fixtures(), 
            "assembly_fixtures": generate_assembly_fixtures(),
            "ci_test_data": create_ci_test_data(),
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0",
                "description": "Test fixtures for Fusion 360 Co-Pilot development",
                "total_fixtures": 0  # Will be calculated
            }
        }
        
        # Calculate total fixtures
        total = (len(all_fixtures["basic_fixtures"]) + 
                len(all_fixtures["complex_fixtures"]) +
                len(all_fixtures["assembly_fixtures"]))
        all_fixtures["metadata"]["total_fixtures"] = total
        
        # Write JSON file
        json_file = output_dir / "test_fixtures.json"
        with open(json_file, 'w') as f:
            json.dump(all_fixtures, f, indent=2)
        
        if args.verbose:
            print(f"Generated JSON fixtures: {json_file} ({total} fixtures)")
    
    # Generate instructions
    if args.format in ["instructions", "both"]:
        instructions_file = output_dir / "STEP_creation_instructions.md"
        with open(instructions_file, 'w') as f:
            f.write(generate_step_file_instructions())
        
        if args.verbose:
            print(f"Generated instructions: {instructions_file}")
    
    # Create a simple README
    readme_file = output_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write("""# Test Fixtures

This directory contains test fixtures for the Fusion 360 Co-Pilot development.

## Contents

- `test_fixtures.json` - Metadata for all test fixtures
- `STEP_creation_instructions.md` - Instructions for creating actual STEP files
- `README.md` - This file

## Usage

### For Development
Use the JSON metadata for lightweight testing without requiring actual CAD files.

### For Full Testing  
Follow the instructions to create actual STEP files in Fusion 360, then place them in this directory.

### For CI/CD
The CI test data in the JSON file provides validation scenarios that can run without CAD software.

## File Naming Convention

- Simple fixtures: `{name}.step` (e.g., `simple_plate.step`)
- Complex fixtures: `{name}.step` (e.g., `mounting_plate_4holes.step`)
- Metadata: `{name}_metadata.json` (optional, for additional data)

Generated by: Fusion 360 Co-Pilot Test Fixture Generator
""")
    
    if args.verbose:
        print(f"Generated README: {readme_file}")
        print("Test fixture generation complete!")
    
    print(f"Test fixtures generated in: {output_dir}")
    print("Run 'python generate_test_fixtures.py --help' for more options")


if __name__ == "__main__":
    main()
