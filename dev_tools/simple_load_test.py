#!/usr/bin/env python3
"""
Fusion 360 Co-Pilot Simple Load Testing Script

This script performs load testing without external dependencies,
focusing on the core validation and execution logic.

Usage:
    python simple_load_test.py [--operations 50] [--verbose]

Author: Fusion CoPilot Team
License: MIT
"""

import time
import json
import statistics
import argparse
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "fusion_addin"))

try:
    from sanitizer import PlanSanitizer
    from executor import PlanExecutor
    MODULES_AVAILABLE = True
    print("✅ Co-Pilot modules loaded successfully")
except ImportError as e:
    MODULES_AVAILABLE = False
    print(f"⚠️ Co-Pilot modules not available: {e}")


@dataclass
class TestResult:
    """Result of a single test operation."""
    test_name: str
    duration: float
    success: bool
    error: Optional[str] = None
    operations_count: int = 0


class MockPlanGenerator:
    """Generates mock CAD plans for testing."""
    
    def __init__(self):
        self.plan_templates = {
            "simple_plate": {
                "plan_id": "simple_plate_001",
                "metadata": {
                    "estimated_duration_seconds": 15,
                    "confidence_score": 0.95,
                    "units": "mm"
                },
                "operations": [
                    {
                        "op_id": "op_1",
                        "op": "create_sketch",
                        "params": {"plane": "XY", "name": "base_sketch"}
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
            },
            
            "complex_bracket": {
                "plan_id": "complex_bracket_001",
                "metadata": {
                    "estimated_duration_seconds": 45,
                    "confidence_score": 0.85,
                    "units": "mm"
                },
                "operations": [
                    {
                        "op_id": "op_1",
                        "op": "create_sketch",
                        "params": {"plane": "XY", "name": "base_sketch"}
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
                            "distance": {"value": 20, "unit": "mm"},
                            "direction": "positive",
                            "operation": "new_body"
                        },
                        "dependencies": ["op_2"]
                    },
                    {
                        "op_id": "op_4",
                        "op": "create_sketch",
                        "params": {"plane": "top_face", "name": "holes_sketch"}
                    },
                    {
                        "op_id": "op_5",
                        "op": "draw_circle",
                        "params": {
                            "center_point": {"x": 30, "y": 15, "z": 0},
                            "radius": {"value": 4, "unit": "mm"}
                        },
                        "target_ref": "holes_sketch",
                        "dependencies": ["op_4"]
                    },
                    {
                        "op_id": "op_6",
                        "op": "pattern_linear",
                        "params": {
                            "entities": ["circle_1"],
                            "direction_1": {"x": 1, "y": 0, "z": 0},
                            "distance_1": {"value": 40, "unit": "mm"},
                            "count_1": 2,
                            "direction_2": {"x": 0, "y": 1, "z": 0},
                            "distance_2": {"value": 20, "unit": "mm"},
                            "count_2": 2
                        },
                        "dependencies": ["op_5"]
                    },
                    {
                        "op_id": "op_7",
                        "op": "cut",
                        "params": {
                            "profile": "holes_sketch",
                            "distance": {"value": 20, "unit": "mm"},
                            "direction": "negative"
                        },
                        "dependencies": ["op_6"]
                    },
                    {
                        "op_id": "op_8", 
                        "op": "fillet",
                        "params": {
                            "edges": ["edge_1", "edge_2", "edge_3", "edge_4"],
                            "radius": {"value": 5, "unit": "mm"}
                        },
                        "dependencies": ["op_7"]
                    }
                ]
            },
            
            "gear_assembly": {
                "plan_id": "gear_assembly_001", 
                "metadata": {
                    "estimated_duration_seconds": 90,
                    "confidence_score": 0.75,
                    "units": "mm"
                },
                "operations": [
                    # Main gear operations
                    {
                        "op_id": "op_1",
                        "op": "create_sketch",
                        "params": {"plane": "XY", "name": "main_gear_sketch"}
                    },
                    {
                        "op_id": "op_2",
                        "op": "draw_circle",
                        "params": {
                            "center_point": {"x": 0, "y": 0, "z": 0},
                            "radius": {"value": 25, "unit": "mm"}
                        },
                        "target_ref": "main_gear_sketch",
                        "dependencies": ["op_1"]
                    },
                    {
                        "op_id": "op_3",
                        "op": "extrude",
                        "params": {
                            "profile": "main_gear_sketch",
                            "distance": {"value": 10, "unit": "mm"},
                            "operation": "new_body"
                        },
                        "dependencies": ["op_2"]
                    },
                    
                    # Pinion gear operations  
                    {
                        "op_id": "op_4",
                        "op": "create_sketch",
                        "params": {"plane": "XY", "name": "pinion_gear_sketch"}
                    },
                    {
                        "op_id": "op_5",
                        "op": "draw_circle",
                        "params": {
                            "center_point": {"x": 37.5, "y": 0, "z": 0},
                            "radius": {"value": 12.5, "unit": "mm"}
                        },
                        "target_ref": "pinion_gear_sketch", 
                        "dependencies": ["op_4"]
                    },
                    {
                        "op_id": "op_6",
                        "op": "extrude",
                        "params": {
                            "profile": "pinion_gear_sketch",
                            "distance": {"value": 10, "unit": "mm"},
                            "operation": "new_body"
                        },
                        "dependencies": ["op_5"]
                    },
                    
                    # Gear teeth (simplified)
                    {
                        "op_id": "op_7",
                        "op": "create_sketch",
                        "params": {"plane": "top_face", "name": "main_teeth_sketch"}
                    },
                    {
                        "op_id": "op_8",
                        "op": "draw_rectangle",
                        "params": {
                            "center_point": {"x": 24, "y": 0, "z": 0},
                            "width": {"value": 2, "unit": "mm"},
                            "height": {"value": 3, "unit": "mm"}
                        },
                        "target_ref": "main_teeth_sketch",
                        "dependencies": ["op_7"]
                    },
                    {
                        "op_id": "op_9", 
                        "op": "pattern_circular",
                        "params": {
                            "entities": ["rectangle_1"],
                            "axis": {"x": 0, "y": 0, "z": 1},
                            "count": 20,
                            "angle": {"value": 360, "unit": "deg"}
                        },
                        "dependencies": ["op_8"]
                    },
                    {
                        "op_id": "op_10",
                        "op": "cut",
                        "params": {
                            "profile": "main_teeth_sketch",
                            "distance": {"value": 2, "unit": "mm"}
                        },
                        "dependencies": ["op_9"]
                    },
                    
                    # Central holes
                    {
                        "op_id": "op_11",
                        "op": "create_sketch", 
                        "params": {"plane": "top_face", "name": "center_holes_sketch"}
                    },
                    {
                        "op_id": "op_12",
                        "op": "draw_circle",
                        "params": {
                            "center_point": {"x": 0, "y": 0, "z": 0},
                            "radius": {"value": 5, "unit": "mm"}
                        },
                        "target_ref": "center_holes_sketch",
                        "dependencies": ["op_11"]
                    },
                    {
                        "op_id": "op_13",
                        "op": "cut",
                        "params": {
                            "profile": "center_holes_sketch",
                            "distance": {"value": 10, "unit": "mm"},
                            "direction": "negative"
                        },
                        "dependencies": ["op_12"]
                    }
                ]
            }
        }
    
    def get_plan(self, plan_type: str) -> Dict[str, Any]:
        """Get a plan by type."""
        return self.plan_templates.get(plan_type, self.plan_templates["simple_plate"]).copy()
    
    def get_all_plans(self) -> Dict[str, Dict[str, Any]]:
        """Get all plan templates."""
        return self.plan_templates.copy()


class SimpleLoadTester:
    """Simple load tester for core Co-Pilot functionality."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.plan_generator = MockPlanGenerator()
        
        # Initialize modules if available
        if MODULES_AVAILABLE:
            try:
                self.sanitizer = PlanSanitizer()
                print("✅ Plan sanitizer initialized")
                
                # Create executor in mock mode
                self.executor = PlanExecutor()
                print("✅ Plan executor initialized")
                
            except Exception as e:
                print(f"⚠️ Could not initialize modules: {e}")
                self.sanitizer = None
                self.executor = None
        else:
            self.sanitizer = None
            self.executor = None
    
    def test_plan_validation(self, plan: Dict[str, Any], test_name: str) -> TestResult:
        """Test plan validation performance."""
        start_time = time.time()
        
        try:
            if self.sanitizer:
                # Use real sanitizer
                is_valid, sanitized_plan, errors = self.sanitizer.sanitize_plan(plan)
                success = is_valid
            else:
                # Mock validation
                success = "operations" in plan and len(plan["operations"]) > 0
                time.sleep(0.01)  # Simulate processing time
            
            duration = time.time() - start_time
            
            return TestResult(
                test_name=f"validation_{test_name}",
                duration=duration,
                success=success,
                operations_count=len(plan.get("operations", []))
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            return TestResult(
                test_name=f"validation_{test_name}",
                duration=duration,
                success=False,
                error=str(e),
                operations_count=len(plan.get("operations", []))
            )
    
    def test_plan_execution(self, plan: Dict[str, Any], test_name: str) -> TestResult:
        """Test plan execution performance."""
        start_time = time.time()
        
        try:
            if self.executor:
                # Use real executor
                result = self.executor.execute_plan(plan)
                success = result.get("success", False)
            else:
                # Mock execution - simulate processing time based on operation count
                op_count = len(plan.get("operations", []))
                time.sleep(op_count * 0.01)  # 10ms per operation
                success = True
            
            duration = time.time() - start_time
            
            return TestResult(
                test_name=f"execution_{test_name}",
                duration=duration,
                success=success,
                operations_count=len(plan.get("operations", []))
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            return TestResult(
                test_name=f"execution_{test_name}",
                duration=duration,
                success=False,
                error=str(e),
                operations_count=len(plan.get("operations", []))
            )
    
    def run_comprehensive_test(self, iterations: int = 10):
        """Run comprehensive test of all plan types."""
        print(f"🧪 Running comprehensive load test ({iterations} iterations per plan type)")
        
        plans = self.plan_generator.get_all_plans()
        
        for plan_type, plan_template in plans.items():
            print(f"\n📋 Testing plan type: {plan_type}")
            
            # Test each plan type multiple times
            for i in range(iterations):
                plan = plan_template.copy()  # Fresh copy for each test
                
                # Test validation
                validation_result = self.test_plan_validation(plan, f"{plan_type}_{i}")
                self.results.append(validation_result)
                
                # Test execution (only if validation succeeded)
                if validation_result.success:
                    execution_result = self.test_plan_execution(plan, f"{plan_type}_{i}")
                    self.results.append(execution_result)
                
                if self.verbose:
                    val_status = "✅" if validation_result.success else "❌"
                    exec_status = "✅" if validation_result.success and execution_result.success else "❌"
                    print(f"  Iteration {i+1}: {val_status} Val({validation_result.duration:.3f}s) {exec_status} Exec({execution_result.duration:.3f}s)" if validation_result.success else f"  Iteration {i+1}: {val_status} Val({validation_result.duration:.3f}s)")
    
    def run_stress_test(self, operations: int = 100):
        """Run stress test with many operations."""
        print(f"🔥 Running stress test ({operations} operations)")
        
        # Get the most complex plan
        gear_plan = self.plan_generator.get_plan("gear_assembly")
        
        for i in range(operations):
            # Test validation and execution
            validation_result = self.test_plan_validation(gear_plan, f"stress_{i}")
            self.results.append(validation_result)
            
            if validation_result.success:
                execution_result = self.test_plan_execution(gear_plan, f"stress_{i}")
                self.results.append(execution_result)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Completed {i + 1}/{operations} operations")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.results:
            return {"error": "No test results available"}
        
        # Separate validation and execution results
        validation_results = [r for r in self.results if r.test_name.startswith("validation_")]
        execution_results = [r for r in self.results if r.test_name.startswith("execution_")]
        
        # Calculate statistics
        def calc_stats(results: List[TestResult], metric: str) -> Dict[str, float]:
            successful = [r for r in results if r.success]
            if not successful:
                return {"count": 0, "min": 0, "max": 0, "mean": 0, "median": 0}
            
            if metric == "duration":
                values = [r.duration for r in successful]
            elif metric == "operations":
                values = [r.operations_count for r in successful]
            else:
                values = []
            
            if not values:
                return {"count": 0, "min": 0, "max": 0, "mean": 0, "median": 0}
            
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values), 
                "mean": statistics.mean(values),
                "median": statistics.median(values)
            }
        
        # Error analysis
        errors = {}
        for result in self.results:
            if not result.success and result.error:
                error_type = result.error.split(':')[0] if ':' in result.error else result.error
                errors[error_type] = errors.get(error_type, 0) + 1
        
        # Performance analysis by operation complexity
        complexity_analysis = {}
        for result in [r for r in self.results if r.success]:
            if result.operations_count <= 3:
                complexity = "simple"
            elif result.operations_count <= 8:
                complexity = "medium" 
            else:
                complexity = "complex"
            
            if complexity not in complexity_analysis:
                complexity_analysis[complexity] = []
            complexity_analysis[complexity].append(result.duration)
        
        # Generate recommendations
        recommendations = []
        
        # Check validation performance
        val_durations = [r.duration for r in validation_results if r.success]
        if val_durations and statistics.mean(val_durations) > 0.1:
            recommendations.append("Validation is slow (>100ms avg). Consider optimizing schema validation.")
        
        # Check execution performance
        exec_durations = [r.duration for r in execution_results if r.success]
        if exec_durations and statistics.mean(exec_durations) > 1.0:
            recommendations.append("Execution simulation is slow (>1s avg). Consider async processing.")
        
        # Check success rates
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.success])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate < 95:
            recommendations.append(f"Low success rate ({success_rate:.1f}%). Review error handling.")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable limits for production use.")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "test_configuration": {
                "modules_available": MODULES_AVAILABLE,
                "total_tests": total_tests
            },
            "summary": {
                "total_operations": total_tests,
                "successful_operations": successful_tests,
                "success_rate": success_rate,
                "total_duration": sum(r.duration for r in self.results)
            },
            "performance": {
                "validation": calc_stats(validation_results, "duration"),
                "execution": calc_stats(execution_results, "duration"),
                "operations_per_test": calc_stats(self.results, "operations")
            },
            "complexity_analysis": {
                complexity: {
                    "count": len(durations),
                    "mean_duration": statistics.mean(durations) if durations else 0,
                    "max_duration": max(durations) if durations else 0
                }
                for complexity, durations in complexity_analysis.items()
            },
            "errors": errors,
            "recommendations": recommendations
        }
        
        return report


def main():
    """Main entry point for simple load testing."""
    parser = argparse.ArgumentParser(description='Fusion 360 Co-Pilot Simple Load Testing')
    parser.add_argument('--operations', type=int, default=50, help='Number of operations for stress test')
    parser.add_argument('--iterations', type=int, default=10, help='Iterations per plan type')
    parser.add_argument('--test-type', choices=['comprehensive', 'stress'], default='comprehensive', help='Type of test to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output', '-o', help='Output report to file (JSON)')
    
    args = parser.parse_args()
    
    print(f"🧪 Fusion 360 Co-Pilot Simple Load Test")
    print(f"⚙️ Test Type: {args.test_type}")
    print(f"🔧 Modules Available: {MODULES_AVAILABLE}")
    print(f"=" * 60)
    
    # Initialize tester
    tester = SimpleLoadTester(args.verbose)
    
    # Run selected test
    start_time = time.time()
    
    try:
        if args.test_type == 'comprehensive':
            tester.run_comprehensive_test(args.iterations)
        else:  # stress
            tester.run_stress_test(args.operations)
        
        end_time = time.time()
        print(f"\n✅ Load testing completed in {end_time - start_time:.2f}s")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Load testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Load testing failed: {e}")
        return 1
    
    # Generate and display report
    report = tester.generate_report()
    
    print(f"\n" + "=" * 60)
    print(f"📊 LOAD TEST REPORT")
    print(f"Total Operations: {report['summary']['total_operations']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Total Duration: {report['summary']['total_duration']:.2f}s")
    
    if report['performance']['validation']['count'] > 0:
        print(f"Avg Validation: {report['performance']['validation']['mean']:.3f}s")
    
    if report['performance']['execution']['count'] > 0:
        print(f"Avg Execution: {report['performance']['execution']['mean']:.3f}s")
    
    # Complexity analysis
    if report.get('complexity_analysis'):
        print(f"\n📈 COMPLEXITY ANALYSIS:")
        for complexity, stats in report['complexity_analysis'].items():
            print(f"  {complexity.capitalize()}: {stats['count']} tests, avg {stats['mean_duration']:.3f}s")
    
    # Errors
    if report.get('errors'):
        print(f"\n❌ ERRORS:")
        for error_type, count in report['errors'].items():
            print(f"  • {error_type}: {count}")
    
    # Recommendations
    if report.get('recommendations'):
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Save report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {args.output}")
    
    # Return appropriate exit code
    success_rate = report['summary']['success_rate']
    if success_rate < 90:
        print(f"\n❌ Load test failed (success rate: {success_rate:.1f}%)")
        return 1
    elif success_rate < 98:
        print(f"\n⚠️ Load test passed with warnings (success rate: {success_rate:.1f}%)")
        return 2
    else:
        print(f"\n✅ Load test passed successfully!")
        return 0


if __name__ == '__main__':
    sys.exit(main())