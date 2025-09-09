#!/usr/bin/env python3
"""
Fusion 360 Co-Pilot Load Testing Script

This script performs comprehensive load testing on the Co-Pilot system to ensure
it can handle complex CAD operations and high throughput scenarios.

Usage:
    python load_test.py [--concurrent 5] [--duration 60] [--verbose]

Author: Fusion CoPilot Team
License: MIT
"""

import asyncio
import aiohttp
import time
import json
import statistics
import argparse
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import concurrent.futures
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "fusion_addin"))

try:
    from sanitizer import PlanSanitizer
    from executor import PlanExecutor
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    print("Warning: Co-Pilot modules not available, using mock implementations")


@dataclass
class LoadTestResult:
    """Result of a single load test operation."""
    test_name: str
    start_time: float
    end_time: float
    success: bool
    error: Optional[str] = None
    response_size: int = 0
    operations_count: int = 0
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class ComplexOperationGenerator:
    """Generates complex CAD operations for load testing."""
    
    def __init__(self):
        self.operation_templates = [
            {
                "name": "complex_bracket",
                "prompt": "Create a mounting bracket 100x50x20mm with 4 holes (8mm diameter) and rounded corners (5mm radius)",
                "expected_ops": 8,
                "complexity": "medium"
            },
            {
                "name": "gear_assembly", 
                "prompt": "Design a gear assembly with main gear (50mm diameter, 20 teeth) and pinion gear (25mm diameter, 10 teeth) with proper spacing",
                "expected_ops": 12,
                "complexity": "high"
            },
            {
                "name": "housing_complex",
                "prompt": "Create a housing 80x60x40mm with internal cavity, mounting bosses, and ventilation slots",
                "expected_ops": 15,
                "complexity": "high"
            },
            {
                "name": "simple_plate",
                "prompt": "Create a rectangular plate 100x50x5mm",
                "expected_ops": 3,
                "complexity": "low"
            },
            {
                "name": "cylinder_with_features",
                "prompt": "Make a cylinder 30mm diameter, 50mm height with 6mm hole through center and 2mm chamfer on edges",
                "expected_ops": 6,
                "complexity": "medium"
            },
            {
                "name": "multi_extrude",
                "prompt": "Create a stepped shaft with diameters 20mm, 15mm, 10mm, lengths 30mm, 20mm, 15mm respectively",
                "expected_ops": 9,
                "complexity": "medium"
            },
            {
                "name": "pattern_operations",
                "prompt": "Create a plate 200x100x10mm with circular pattern of 8 holes (5mm diameter) on 60mm bolt circle",
                "expected_ops": 7,
                "complexity": "medium"
            },
            {
                "name": "complex_shell",
                "prompt": "Design a container 100x100x80mm with 3mm wall thickness, rounded corners, and removable lid",
                "expected_ops": 18,
                "complexity": "high"
            }
        ]
    
    def get_operation(self, complexity: str = None) -> Dict[str, Any]:
        """Get a random operation, optionally filtered by complexity."""
        if complexity:
            filtered = [op for op in self.operation_templates if op["complexity"] == complexity]
            import random
            return random.choice(filtered) if filtered else self.operation_templates[0]
        
        import random
        return random.choice(self.operation_templates)
    
    def get_all_operations(self) -> List[Dict[str, Any]]:
        """Get all operation templates."""
        return self.operation_templates.copy()


class LoadTester:
    """Comprehensive load testing framework for Fusion 360 Co-Pilot."""
    
    def __init__(self, endpoint: str = "http://localhost:8080/llm", verbose: bool = False):
        self.endpoint = endpoint
        self.verbose = verbose
        self.results: List[LoadTestResult] = []
        self.operation_generator = ComplexOperationGenerator()
        
        # Performance tracking
        self.start_time = None
        self.end_time = None
        
        # Initialize modules if available
        if MODULES_AVAILABLE:
            try:
                self.sanitizer = PlanSanitizer()
                self.executor = PlanExecutor()  # Mock mode by default
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Could not initialize modules: {e}")
                self.sanitizer = None
                self.executor = None
        else:
            self.sanitizer = None
            self.executor = None
    
    async def send_llm_request(self, prompt: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Send a request to the LLM endpoint."""
        payload = {
            "prompt": prompt,
            "context": {
                "units": "mm",
                "max_operations": 50
            }
        }
        
        async with session.post(self.endpoint, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
    
    def validate_plan(self, plan: Dict[str, Any]) -> bool:
        """Validate a plan using the sanitizer if available."""
        if not self.sanitizer:
            # Basic validation without sanitizer
            required_fields = ["plan_id", "metadata", "operations"]
            return all(field in plan for field in required_fields)
        
        try:
            # Use actual sanitizer
            validated_plan = self.sanitizer.validate_plan(plan)
            return validated_plan is not None
        except Exception as e:
            if self.verbose:
                print(f"Validation failed: {e}")
            return False
    
    def simulate_execution(self, plan: Dict[str, Any]) -> bool:
        """Simulate plan execution."""
        if not self.executor:
            # Mock execution - just check plan structure
            return len(plan.get("operations", [])) > 0
        
        try:
            # Use actual executor in mock mode
            result = self.executor.execute_plan(plan, preview_mode=True)
            return result.get("success", False)
        except Exception as e:
            if self.verbose:
                print(f"Execution simulation failed: {e}")
            return False
    
    async def run_single_test(self, operation: Dict[str, Any], session: aiohttp.ClientSession) -> LoadTestResult:
        """Run a single load test operation."""
        start_time = time.time()
        
        try:
            # Send LLM request
            response = await self.send_llm_request(operation["prompt"], session)
            
            # Validate response
            if not self.validate_plan(response):
                raise Exception("Plan validation failed")
            
            # Simulate execution
            if not self.simulate_execution(response):
                raise Exception("Plan execution simulation failed")
            
            end_time = time.time()
            
            return LoadTestResult(
                test_name=operation["name"],
                start_time=start_time,
                end_time=end_time,
                success=True,
                response_size=len(json.dumps(response)),
                operations_count=len(response.get("operations", []))
            )
            
        except Exception as e:
            end_time = time.time()
            
            return LoadTestResult(
                test_name=operation["name"],
                start_time=start_time,
                end_time=end_time,
                success=False,
                error=str(e)
            )
    
    async def run_concurrent_test(self, concurrent_users: int = 5, duration: int = 60):
        """Run concurrent load test."""
        print(f"🚀 Starting concurrent load test: {concurrent_users} users, {duration}s duration")
        
        self.start_time = time.time()
        end_time = self.start_time + duration
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            tasks = []
            
            # Create concurrent user tasks
            for user_id in range(concurrent_users):
                task = asyncio.create_task(self.run_user_simulation(user_id, end_time, session))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
        
        self.end_time = time.time()
    
    async def run_user_simulation(self, user_id: int, end_time: float, session: aiohttp.ClientSession):
        """Simulate a single user's load testing session."""
        user_results = []
        
        while time.time() < end_time:
            # Select operation based on realistic usage patterns
            # 60% simple, 30% medium, 10% complex
            import random
            rand = random.random()
            if rand < 0.6:
                operation = self.operation_generator.get_operation("low")
            elif rand < 0.9:
                operation = self.operation_generator.get_operation("medium")
            else:
                operation = self.operation_generator.get_operation("high")
            
            # Add user context to operation name
            operation = operation.copy()
            operation["name"] = f"user{user_id}_{operation['name']}"
            
            # Run the test
            result = await self.run_single_test(operation, session)
            user_results.append(result)
            self.results.append(result)
            
            if self.verbose:
                status = "✅" if result.success else "❌"
                print(f"{status} {result.test_name}: {result.duration:.2f}s")
            
            # Small delay between operations (realistic user behavior)
            await asyncio.sleep(random.uniform(1, 3))
    
    async def run_stress_test(self, max_concurrent: int = 20, ramp_up_time: int = 30):
        """Run stress test with gradually increasing load."""
        print(f"🔥 Starting stress test: ramp up to {max_concurrent} users over {ramp_up_time}s")
        
        self.start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            tasks = []
            
            # Gradual ramp up
            for i in range(max_concurrent):
                delay = (ramp_up_time / max_concurrent) * i
                task = asyncio.create_task(self.run_delayed_user(i, delay, session))
                tasks.append(task)
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
        
        self.end_time = time.time()
    
    async def run_delayed_user(self, user_id: int, delay: float, session: aiohttp.ClientSession):
        """Run user simulation with initial delay."""
        await asyncio.sleep(delay)
        
        # Run for 60 seconds after delay
        end_time = time.time() + 60
        await self.run_user_simulation(user_id, end_time, session)
    
    def run_sequential_test(self):
        """Run sequential test of all operation types."""
        print("📋 Running sequential test of all operations...")
        
        self.start_time = time.time()
        
        # Use sync session for sequential testing
        import requests
        
        for operation in self.operation_generator.get_all_operations():
            start_time = time.time()
            
            try:
                # Send request
                payload = {
                    "prompt": operation["prompt"],
                    "context": {
                        "units": "mm",
                        "max_operations": 50
                    }
                }
                
                response = requests.post(self.endpoint, json=payload, timeout=30)
                response.raise_for_status()
                plan = response.json()
                
                # Validate and simulate execution
                if not self.validate_plan(plan):
                    raise Exception("Plan validation failed")
                
                if not self.simulate_execution(plan):
                    raise Exception("Plan execution simulation failed")
                
                end_time = time.time()
                
                result = LoadTestResult(
                    test_name=operation["name"],
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                    response_size=len(json.dumps(plan)),
                    operations_count=len(plan.get("operations", []))
                )
                
            except Exception as e:
                end_time = time.time()
                
                result = LoadTestResult(
                    test_name=operation["name"],
                    start_time=start_time,
                    end_time=end_time,
                    success=False,
                    error=str(e)
                )
            
            self.results.append(result)
            
            if self.verbose:
                status = "✅" if result.success else "❌"
                print(f"{status} {result.test_name}: {result.duration:.2f}s ({result.operations_count} ops)")
        
        self.end_time = time.time()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive load test report."""
        if not self.results:
            return {"error": "No test results available"}
        
        # Calculate statistics
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        durations = [r.duration for r in successful_results]
        operation_counts = [r.operations_count for r in successful_results]
        response_sizes = [r.response_size for r in successful_results]
        
        # Performance metrics
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        requests_per_second = len(self.results) / total_duration if total_duration > 0 else 0
        
        # Error analysis
        error_summary = {}
        for result in failed_results:
            error_type = type(Exception(result.error)).__name__ if result.error else "Unknown"
            error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test_configuration": {
                "endpoint": self.endpoint,
                "total_duration": total_duration,
                "modules_available": MODULES_AVAILABLE
            },
            "summary": {
                "total_requests": len(self.results),
                "successful_requests": len(successful_results),
                "failed_requests": len(failed_results),
                "success_rate": len(successful_results) / len(self.results) * 100,
                "requests_per_second": requests_per_second
            },
            "performance": {
                "response_times": {
                    "min": min(durations) if durations else 0,
                    "max": max(durations) if durations else 0,
                    "mean": statistics.mean(durations) if durations else 0,
                    "median": statistics.median(durations) if durations else 0,
                    "p95": self._percentile(durations, 95) if durations else 0,
                    "p99": self._percentile(durations, 99) if durations else 0
                },
                "operations_per_request": {
                    "min": min(operation_counts) if operation_counts else 0,
                    "max": max(operation_counts) if operation_counts else 0,
                    "mean": statistics.mean(operation_counts) if operation_counts else 0
                },
                "response_sizes": {
                    "min": min(response_sizes) if response_sizes else 0,
                    "max": max(response_sizes) if response_sizes else 0,
                    "mean": statistics.mean(response_sizes) if response_sizes else 0
                }
            },
            "errors": error_summary,
            "recommendations": self._get_performance_recommendations(successful_results, failed_results)
        }
        
        return report
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_performance_recommendations(self, successful: List[LoadTestResult], failed: List[LoadTestResult]) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []
        
        if successful:
            avg_duration = statistics.mean([r.duration for r in successful])
            if avg_duration > 5.0:
                recommendations.append("Response times are high (>5s). Consider optimizing LLM requests or caching.")
        
        failure_rate = len(failed) / (len(successful) + len(failed)) * 100 if (successful or failed) else 0
        if failure_rate > 10:
            recommendations.append(f"High failure rate ({failure_rate:.1f}%). Review error handling and retry logic.")
        
        if failure_rate > 50:
            recommendations.append("Critical failure rate. System may not be ready for production load.")
        
        # Operation complexity analysis
        complex_ops = [r for r in successful if r.operations_count > 10]
        if complex_ops:
            avg_complex_duration = statistics.mean([r.duration for r in complex_ops])
            if avg_complex_duration > 10:
                recommendations.append("Complex operations (>10 ops) are slow. Consider operation batching or async processing.")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable limits for production use.")
        
        return recommendations


async def main():
    """Main entry point for load testing."""
    parser = argparse.ArgumentParser(description='Fusion 360 Co-Pilot Load Testing')
    parser.add_argument('--endpoint', default='http://localhost:8080/llm', help='LLM endpoint to test')
    parser.add_argument('--concurrent', type=int, default=5, help='Number of concurrent users')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--test-type', choices=['concurrent', 'stress', 'sequential'], default='concurrent', help='Type of load test')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output', '-o', help='Output report to file (JSON)')
    
    args = parser.parse_args()
    
    print(f"🧪 Fusion 360 Co-Pilot Load Testing")
    print(f"🎯 Endpoint: {args.endpoint}")
    print(f"⚙️ Type: {args.test_type}")
    print(f"=" * 60)
    
    # Initialize load tester
    tester = LoadTester(args.endpoint, args.verbose)
    
    # Check endpoint availability
    try:
        import requests
        response = requests.get(args.endpoint.replace('/llm', '/health'), timeout=5)
        if response.status_code == 200:
            print("✅ Endpoint is reachable")
        else:
            print("⚠️ Endpoint returned non-200 status")
    except Exception as e:
        print(f"⚠️ Could not verify endpoint: {e}")
        print("Continuing with load test...")
    
    # Run selected test type
    try:
        if args.test_type == 'concurrent':
            await tester.run_concurrent_test(args.concurrent, args.duration)
        elif args.test_type == 'stress':
            await tester.run_stress_test(args.concurrent, args.duration)
        else:  # sequential
            tester.run_sequential_test()
        
        print(f"\n✅ Load testing completed")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Load testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Load testing failed: {e}")
        return 1
    
    # Generate and display report
    report = tester.generate_report()
    
    print(f"\n" + "=" * 60)
    print(f"📊 LOAD TEST REPORT")
    print(f"Total Requests: {report['summary']['total_requests']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    print(f"Requests/sec: {report['summary']['requests_per_second']:.2f}")
    print(f"Avg Response: {report['performance']['response_times']['mean']:.2f}s")
    print(f"P95 Response: {report['performance']['response_times']['p95']:.2f}s")
    
    if report.get('errors'):
        print(f"\n❌ ERRORS:")
        for error_type, count in report['errors'].items():
            print(f"  • {error_type}: {count}")
    
    if report.get('recommendations'):
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {args.output}")
    
    # Return appropriate exit code
    success_rate = report['summary']['success_rate']
    if success_rate < 80:
        print(f"\n❌ Load test failed (success rate: {success_rate:.1f}%)")
        return 1
    elif success_rate < 95:
        print(f"\n⚠️ Load test passed with warnings (success rate: {success_rate:.1f}%)")
        return 2
    else:
        print(f"\n✅ Load test passed successfully!")
        return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))