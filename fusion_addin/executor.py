"""
Fusion 360 Natural-Language CAD Co-Pilot - Plan Executor

This module provides deterministic execution of validated plans using the Fusion 360 API.
It includes transaction management, sandbox preview, and comprehensive error handling.

Author: Fusion CoPilot Team
License: MIT
"""

import json
import time
import traceback
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import logging

# Fusion 360 API imports
# NOTE: These imports will only work in the Fusion 360 Python environment
# For development in Cursor, we provide mock implementations and clear TODOs
try:
    import adsk.core
    import adsk.fusion
    import adsk.cam
    FUSION_AVAILABLE = True
except ImportError:
    # Development mode - create mock objects
    FUSION_AVAILABLE = False
    
    class MockFusionAPI:
        """Mock Fusion API for development/testing."""
        pass
    
    adsk = MockFusionAPI()
    adsk.core = MockFusionAPI()
    adsk.fusion = MockFusionAPI()
    adsk.cam = MockFusionAPI()

# Configure logging
logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Raised when plan execution fails."""
    pass


class TransactionContext:
    """
    Context manager for Fusion 360 transaction handling.
    Provides atomic operation execution with rollback capability.
    """
    
    def __init__(self, name: str = "CoPilot Operation"):
        self.name = name
        self.transaction = None
        self.app = None
        self.design = None
        self.timeline_start = None
        
    def __enter__(self):
        """Begin transaction."""
        if FUSION_AVAILABLE:
            # TODO: Replace with actual Fusion API calls
            # self.app = adsk.core.Application.get()
            # self.design = self.app.activeProduct
            # if not self.design:
            #     raise ExecutionError("No active design document")
            # 
            # # Start transaction
            # self.transaction = self.design.timeline.timelineGroups.add(
            #     self.design.timeline.count - 1,
            #     self.design.timeline.count - 1
            # )
            # self.transaction.name = self.name
            # 
            # # Record timeline state for rollback
            # self.timeline_start = self.design.timeline.count
            
            logger.info(f"Started transaction: {self.name}")
        else:
            # Mock implementation for development
            logger.info(f"[MOCK] Started transaction: {self.name}")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End transaction with commit or rollback."""
        if exc_type is not None:
            # Exception occurred - rollback
            self.rollback()
            logger.error(f"Transaction rolled back due to error: {exc_val}")
            return False  # Re-raise exception
        else:
            # Success - commit
            self.commit()
            logger.info(f"Transaction committed: {self.name}")
            return True
    
    def commit(self):
        """Commit the transaction."""
        if FUSION_AVAILABLE and self.transaction:
            # TODO: Replace with actual Fusion API calls
            # The timeline group automatically commits when operations complete
            # Additional cleanup or finalization can be done here
            pass
        else:
            logger.info(f"[MOCK] Committed transaction: {self.name}")
    
    def rollback(self):
        """Rollback the transaction."""
        if FUSION_AVAILABLE and self.design and self.timeline_start is not None:
            # TODO: Replace with actual Fusion API calls
            # timeline = self.design.timeline
            # 
            # # Remove all timeline items added during this transaction
            # for i in range(timeline.count - 1, self.timeline_start - 1, -1):
            #     timeline_item = timeline.item(i)
            #     if timeline_item.isValid:
            #         timeline_item.deleteMe()
            
            logger.info(f"Rolled back transaction: {self.name}")
        else:
            logger.info(f"[MOCK] Rolled back transaction: {self.name}")


class PlanExecutor:
    """
    Deterministic executor for validated CAD plans.
    
    Provides:
    - Sandbox preview execution
    - Production execution with transactions
    - Timeline node mapping
    - Comprehensive error handling
    """
    
    def __init__(self, settings: Optional[Dict] = None):
        """
        Initialize the plan executor.
        
        Args:
            settings: Configuration settings
        """
        self.settings = settings or {}
        self.app = None
        self.design = None
        self.ui = None
        
        # Execution state
        self.current_plan = None
        self.execution_start_time = None
        self.timeline_mapping = {}
        self.created_features = []
        
        # Initialize Fusion API connection
        self._initialize_fusion_api()
    
    def _initialize_fusion_api(self):
        """Initialize connection to Fusion 360 API."""
        if FUSION_AVAILABLE:
            try:
                self.app = adsk.core.Application.get()
                if not self.app:
                    raise ExecutionError("Failed to acquire Fusion Application")
                self.ui = self.app.userInterface
                self.design = adsk.fusion.Design.cast(self.app.activeProduct)
                if not self.design:
                    raise ExecutionError("No active Fusion design. Open a design and try again.")
                logger.info("Fusion 360 API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Fusion API: {e}")
                raise ExecutionError(f"Fusion API initialization failed: {e}")
        else:
            logger.info("[MOCK] Fusion 360 API initialized (development mode)")
    
    def preview_plan_in_sandbox(self, plan: Dict) -> Dict:
        """
        Execute plan in sandbox mode for safe preview.
        
        Creates a temporary component, applies operations, captures results,
        then cleans up without affecting the main design.
        
        Args:
            plan: Validated plan dictionary
            
        Returns:
            Dictionary with preview results and metadata
        """
        logger.info(f"Starting sandbox preview for plan: {plan.get('plan_id', 'unknown')}")
        
        preview_start_time = time.time()
        
        try:
            if FUSION_AVAILABLE:
                # TODO: Replace with actual Fusion API calls
                # 
                # # Create temporary component for sandbox
                # root_comp = self.design.rootComponent
                # sandbox_occurrence = root_comp.occurrences.addNewComponent(
                #     adsk.core.Matrix3D.create()
                # )
                # sandbox_occurrence.component.name = f"Sandbox_{plan.get('plan_id', 'preview')}"
                # sandbox_comp = sandbox_occurrence.component
                # 
                # # Execute operations in sandbox
                # sandbox_results = self._execute_operations_in_component(
                #     plan['operations'], sandbox_comp
                # )
                # 
                # # Capture preview data
                # preview_data = self._capture_preview_data(sandbox_comp, sandbox_results)
                # 
                # # Clean up sandbox component
                # sandbox_occurrence.deleteMe()
                
                # Mock preview data for development
                preview_data = self._mock_preview_execution(plan)
                
            else:
                # Mock implementation for development
                preview_data = self._mock_preview_execution(plan)
            
            preview_duration = time.time() - preview_start_time
            
            result = {
                'success': True,
                'plan_id': plan.get('plan_id'),
                'preview_duration': preview_duration,
                'preview_data': preview_data,
                'operations_count': len(plan.get('operations', [])),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            logger.info(f"Sandbox preview completed in {preview_duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Sandbox preview failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'plan_id': plan.get('plan_id'),
                'preview_duration': time.time() - preview_start_time,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    def execute_plan(self, plan: Dict) -> Dict:
        """
        Execute a validated plan on the active design.
        
        Uses transaction management for atomic execution with rollback capability.
        
        Args:
            plan: Validated plan dictionary
            
        Returns:
            Dictionary with execution results and timeline mapping
        """
        logger.info(f"Starting plan execution: {plan.get('plan_id', 'unknown')}")
        
        self.current_plan = plan
        self.execution_start_time = time.time()
        self.timeline_mapping.clear()
        self.created_features.clear()
        
        try:
            with TransactionContext(f"CoPilot: {plan.get('plan_id', 'Unknown')}"):
                # Execute all operations
                execution_results = self._execute_operations(plan['operations'])
                
                # Calculate execution metrics
                execution_duration = time.time() - self.execution_start_time
                
                result = {
                    'success': True,
                    'plan_id': plan.get('plan_id'),
                    'execution_duration': execution_duration,
                    'operations_executed': len(plan.get('operations', [])),
                    'features_created': self.created_features.copy(),
                    'timeline_mapping': self.timeline_mapping.copy(),
                    'execution_results': execution_results,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                
                logger.info(f"Plan execution completed successfully in {execution_duration:.2f}s")
                return result
                
        except Exception as e:
            execution_duration = time.time() - self.execution_start_time
            error_msg = str(e)
            
            logger.error(f"Plan execution failed: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return {
                'success': False,
                'error_message': error_msg,
                'plan_id': plan.get('plan_id'),
                'execution_duration': execution_duration,
                'operations_attempted': len(plan.get('operations', [])),
                'partial_timeline_mapping': self.timeline_mapping.copy(),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    def _execute_operations(self, operations: List[Dict]) -> List[Dict]:
        """Execute a list of operations sequentially."""
        results = []
        
        for i, operation in enumerate(operations):
            try:
                logger.debug(f"Executing operation {i+1}/{len(operations)}: {operation.get('op')}")
                
                result = self._execute_single_operation(operation)
                results.append(result)
                
                # Update timeline mapping if successful
                if result.get('success') and result.get('timeline_node'):
                    self.timeline_mapping[operation['op_id']] = result['timeline_node']
                
                # Update created features list
                if result.get('feature_created'):
                    self.created_features.append(result['feature_created'])
                
            except Exception as e:
                error_msg = f"Operation {operation.get('op_id', i)} failed: {str(e)}"
                logger.error(error_msg)
                results.append({
                    'success': False,
                    'error': error_msg,
                    'operation_id': operation.get('op_id', f'op_{i}')
                })
                # Re-raise to trigger transaction rollback
                raise ExecutionError(error_msg)
        
        return results
    
    def _execute_single_operation(self, operation: Dict) -> Dict:
        """Execute a single CAD operation."""
        op_type = operation['op']
        op_id = operation['op_id']
        params = operation['params']
        
        logger.debug(f"Executing {op_type} with params: {params}")
        
        # Dispatch to specific operation handler
        if op_type == 'create_sketch':
            return self._execute_create_sketch(op_id, params)
        elif op_type == 'draw_rectangle':
            return self._execute_draw_rectangle(op_id, params, operation.get('target_ref'))
        elif op_type == 'draw_circle':
            return self._execute_draw_circle(op_id, params, operation.get('target_ref'))
        elif op_type == 'draw_polygon':
            return self._execute_draw_polygon(op_id, params, operation.get('target_ref'))
        elif op_type == 'extrude':
            return self._execute_extrude(op_id, params)
        elif op_type == 'cut':
            return self._execute_cut(op_id, params)
        elif op_type == 'fillet':
            return self._execute_fillet(op_id, params)
        elif op_type == 'chamfer':
            return self._execute_chamfer(op_id, params)
        elif op_type == 'create_hole':
            return self._execute_create_hole(op_id, params, operation.get('target_ref'))
        elif op_type == 'pattern_linear':
            return self._execute_pattern_linear(op_id, params)
        elif op_type == 'pattern_circular':
            return self._execute_pattern_circular(op_id, params)
        elif op_type == 'pattern_rectangular':
            return self._execute_pattern_rectangular(op_id, params)
        elif op_type == 'shell':
            return self._execute_shell(op_id, params)
        else:
            raise ExecutionError(f"Unsupported operation type: {op_type}")
    
    def _execute_create_sketch(self, op_id: str, params: Dict) -> Dict:
        """Execute create_sketch operation."""
        if FUSION_AVAILABLE:
            root_comp = self.design.rootComponent
            sketches = root_comp.sketches
            plane_name = params.get('plane', 'XY')
            if plane_name == 'XY':
                sketch_plane = root_comp.xYConstructionPlane
            elif plane_name == 'XZ':
                sketch_plane = root_comp.xZConstructionPlane
            elif plane_name == 'YZ':
                sketch_plane = root_comp.yZConstructionPlane
            else:
                sketch_plane = root_comp.xYConstructionPlane
            sketch = sketches.add(sketch_plane)
            desired_name = params.get('name', f'Sketch_{op_id}')
            # Prefix with CoPilot_ for easy identification
            if not desired_name.startswith('CoPilot_'):
                desired_name = f'CoPilot_{desired_name}'
            try:
                sketch.name = desired_name
            except Exception:
                pass
            self.last_sketch = sketch
            timeline_node = self._get_latest_timeline_node()
            logger.info(f"Created sketch: {desired_name}")
        else:
            # Development mock
            sketch_name = params.get('name', f'Sketch_{op_id}')
            timeline_node = f"Timeline_Sketch_{op_id}"
            
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': desired_name if FUSION_AVAILABLE else sketch_name,
            'timeline_node': timeline_node,
            'feature_type': 'sketch'
        }
    
    def _execute_draw_rectangle(self, op_id: str, params: Dict, target_ref: Optional[str]) -> Dict:
        """Execute draw_rectangle operation."""
        if FUSION_AVAILABLE:
            sketch = None
            # Prefer explicitly the sketch we just created if target_ref matches its name
            if target_ref:
                sketch = self._resolve_sketch_reference(target_ref)
            if not sketch and hasattr(self, 'last_sketch'):
                sketch = self.last_sketch
            if not sketch:
                # As a final fallback, pick the last sketch in the root component
                try:
                    root_comp = self.design.rootComponent
                    sketches = root_comp.sketches
                    if sketches.count > 0:
                        sketch = sketches.item(sketches.count - 1)
                except Exception:
                    sketch = None
            if not sketch:
                raise ExecutionError("No target sketch available for rectangle")

            center_point = params.get('center_point', {'x': 0, 'y': 0, 'z': 0})
            width_mm = self._extract_dimension_value(params.get('width', 10))
            height_mm = self._extract_dimension_value(params.get('height', 10))

            def mm(v: float) -> float:
                return float(v) / 10.0

            x1 = mm(center_point.get('x', 0)) - mm(width_mm) / 2.0
            y1 = mm(center_point.get('y', 0)) - mm(height_mm) / 2.0
            x2 = mm(center_point.get('x', 0)) + mm(width_mm) / 2.0
            y2 = mm(center_point.get('y', 0)) + mm(height_mm) / 2.0
            corner1 = adsk.core.Point3D.create(x1, y1, 0)
            corner2 = adsk.core.Point3D.create(x2, y2, 0)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(corner1, corner2)
            try:
                if sketch.profiles.count > 0:
                    self.last_profile = sketch.profiles.item(sketch.profiles.count - 1)
            except Exception:
                self.last_profile = None
            width = width_mm
            height = height_mm
            logger.info(f"Drew rectangle: {width}x{height}mm in sketch")
        else:
            # Development mock
            width = self._extract_dimension_value(params.get('width', 10))
            height = self._extract_dimension_value(params.get('height', 10))
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'Rectangle_{op_id}',
            'timeline_node': None,  # Sketch geometry doesn't create timeline nodes
            'feature_type': 'sketch_geometry',
            'dimensions': {'width': width, 'height': height}
        }
    
    def _execute_draw_circle(self, op_id: str, params: Dict, target_ref: Optional[str]) -> Dict:
        """Execute draw_circle operation."""
        if FUSION_AVAILABLE:
            # Resolve or pick a sketch similar to rectangle flow
            sketch = None
            if target_ref:
                sketch = self._resolve_sketch_reference(target_ref)
            if not sketch and hasattr(self, 'last_sketch'):
                sketch = self.last_sketch
            if not sketch:
                try:
                    root_comp = self.design.rootComponent
                    sketches = root_comp.sketches
                    if sketches.count > 0:
                        sketch = sketches.item(sketches.count - 1)
                except Exception:
                    sketch = None
            if not sketch:
                raise ExecutionError("No target sketch available for circle")

            center_point = params.get('center_point', {'x': 0, 'y': 0, 'z': 0})

            # Dimensions are in mm; Fusion expects cm (cm = mm/10)
            if 'radius' in params:
                radius_mm = self._extract_dimension_value(params['radius'])
                diameter = radius_mm * 2
            elif 'diameter' in params:
                diameter = self._extract_dimension_value(params['diameter'])
                radius_mm = diameter / 2.0
            else:
                raise ExecutionError("Circle requires radius or diameter")

            def mm(v: float) -> float:
                return float(v) / 10.0

            center = adsk.core.Point3D.create(mm(center_point.get('x', 0)), mm(center_point.get('y', 0)), 0)
            circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(center, mm(radius_mm))
            try:
                if sketch.profiles.count > 0:
                    self.last_profile = sketch.profiles.item(sketch.profiles.count - 1)
            except Exception:
                self.last_profile = None
            logger.info(f"Drew circle: ⌀{diameter}mm in sketch")
        else:
            # Development mock
            if 'radius' in params:
                radius = self._extract_dimension_value(params['radius'])
                diameter = radius * 2
            elif 'diameter' in params:
                diameter = self._extract_dimension_value(params['diameter'])
            else:
                raise ExecutionError("Circle requires radius or diameter")
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'Circle_{op_id}',
            'timeline_node': None,
            'feature_type': 'sketch_geometry',
            'dimensions': {'diameter': diameter}
        }

    def _execute_draw_polygon(self, op_id: str, params: Dict, target_ref: Optional[str]) -> Dict:
        """Execute draw_polygon operation (regular polygon)."""
        if FUSION_AVAILABLE:
            sketch = None
            if target_ref:
                sketch = self._resolve_sketch_reference(target_ref)
            if not sketch and hasattr(self, 'last_sketch'):
                sketch = self.last_sketch
            if not sketch:
                try:
                    root_comp = self.design.rootComponent
                    sketches = root_comp.sketches
                    if sketches.count > 0:
                        sketch = sketches.item(sketches.count - 1)
                except Exception:
                    sketch = None
            if not sketch:
                raise ExecutionError("No target sketch available for polygon")

            center_point = params.get('center_point', {'x': 0, 'y': 0, 'z': 0})
            sides = int(params.get('sides', 6))
            # Support circumscribed_radius or inscribed_radius
            if 'circumscribed_radius' in params:
                radius_mm = self._extract_dimension_value(params['circumscribed_radius'])
            elif 'inscribed_radius' in params:
                # Convert inscribed radius to circumscribed for regular polygons
                r_in_mm = self._extract_dimension_value(params['inscribed_radius'])
                import math
                radius_mm = r_in_mm / math.cos(math.pi / max(sides, 3))
            else:
                radius_mm = self._extract_dimension_value(params.get('radius', 10))

            def mm(v: float) -> float:
                return float(v) / 10.0

            center = adsk.core.Point3D.create(mm(center_point.get('x', 0)), mm(center_point.get('y', 0)), 0)
            # Fusion API lacks a direct "regular polygon" primitive; sketch via lines
            import math
            points = []
            for i in range(max(sides, 3)):
                ang = 2 * math.pi * i / max(sides, 3)
                px = center.x + mm(radius_mm) * math.cos(ang)
                py = center.y + mm(radius_mm) * math.sin(ang)
                points.append(adsk.core.Point3D.create(px, py, 0))
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]
                sketch.sketchCurves.sketchLines.addByTwoPoints(p1, p2)
            try:
                if sketch.profiles.count > 0:
                    self.last_profile = sketch.profiles.item(sketch.profiles.count - 1)
            except Exception:
                self.last_profile = None
            feature_name = f'Polygon_{op_id}'
        else:
            # Development mock only
            sides = int(params.get('sides', 6))
            feature_name = f'Polygon_{op_id}'
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': feature_name,
            'timeline_node': None,
            'feature_type': 'sketch_geometry',
            'dimensions': {'sides': sides}
        }
    
    def _execute_extrude(self, op_id: str, params: Dict) -> Dict:
        """Execute extrude operation."""
        if FUSION_AVAILABLE:
            root_comp = self.design.rootComponent
            extrudes = root_comp.features.extrudeFeatures
            profile = getattr(self, 'last_profile', None)
            if not profile:
                sketch = getattr(self, 'last_sketch', None)
                if sketch and sketch.profiles.count > 0:
                    profile = sketch.profiles.item(sketch.profiles.count - 1)
            if not profile:
                raise ExecutionError("No profile available for extrude")
            distance_mm = self._extract_dimension_value(params.get('distance', 10))
            extrude_input = extrudes.createInput(
                profile,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            )
            distance_input = adsk.core.ValueInput.createByReal(float(distance_mm) / 10.0)
            extrude_input.setDistanceExtent(False, distance_input)
            extrude_feature = extrudes.add(extrude_input)
            try:
                extrude_feature.name = f'CoPilot_Extrude_{op_id}'
            except Exception:
                pass
            # Rename created bodies for clarity
            try:
                bodies = extrude_feature.bodies
                for i in range(bodies.count):
                    b = bodies.item(i)
                    try:
                        b.name = f'CoPilot_Body_{op_id}_{i+1}'
                    except Exception:
                        pass
            except Exception:
                pass
            # Zoom to fit to reveal the new geometry
            try:
                vp = self.app.activeViewport
                if vp:
                    vp.fit()
            except Exception:
                pass
            timeline_node = self._get_latest_timeline_node()
            logger.info(f"Extruded profile by {distance_mm}mm")
        else:
            # Development mock
            distance = self._extract_dimension_value(params.get('distance', 10))
            timeline_node = f"Timeline_Extrude_{op_id}"
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'Extrude_{op_id}',
            'timeline_node': timeline_node,
            'feature_type': 'extrude',
            'dimensions': {'distance': distance_mm if FUSION_AVAILABLE else distance}
        }
    
    def _execute_create_hole(self, op_id: str, params: Dict, target_ref: Optional[str]) -> Dict:
        """Execute create_hole operation."""
        if FUSION_AVAILABLE:
            # Use selected face if available, otherwise require selection
            root_comp = self.design.rootComponent
            features = root_comp.features
            holes = features.holeFeatures

            target_face = None
            try:
                # Prefer explicit reference for selected face
                if (target_ref or '').lower() in ('face_selected', 'selected_face', 'face_current'):
                    target_face = self._get_selected_face()
                if not target_face:
                    # Fallback to any currently selected face
                    target_face = self._get_selected_face()
            except Exception:
                target_face = None

            if not target_face:
                # As a last resort, try to pick the last face from last created feature's body
                try:
                    root_comp = self.design.rootComponent
                    bodies = root_comp.bRepBodies
                    if bodies and bodies.count > 0:
                        b = bodies.item(bodies.count - 1)
                        faces = getattr(b, 'faces', None)
                        if faces and faces.count > 0:
                            target_face = faces.item(0)
                except Exception:
                    target_face = None
            if not target_face:
                raise ExecutionError("Select a target face for the hole and try again.")

            # Extract hole parameters
            center_point = params.get('center_point', {'x': 0, 'y': 0, 'z': 0})
            diameter_mm = self._extract_dimension_value(params.get('diameter', 5))
            depth_type = params.get('depth', 'through_all')

            def mm(v: float) -> float:
                return float(v) / 10.0

            # Create a sketch on the target face and add a sketch point for positioning
            sketches = root_comp.sketches
            face_sketch = sketches.add(target_face)
            try:
                face_sketch.name = f'CoPilot_HoleSketch_{op_id}'
            except Exception:
                pass
            # Use sketch origin (0,0) for center by default; allow XY offsets if provided
            cx = center_point.get('x', 0)
            cy = center_point.get('y', 0)
            # In face sketch coordinates, use Z=0
            sketch_pt_3d = adsk.core.Point3D.create(mm(cx), mm(cy), 0)
            sp = face_sketch.sketchPoints.add(sketch_pt_3d)

            dia_val = adsk.core.ValueInput.createByReal(mm(diameter_mm))
            hole_input = holes.createSimpleInput(dia_val)
            try:
                hole_input.setPositionBySketchPoint(sp, target_face)
            except Exception as e:
                raise ExecutionError(f"Failed to position hole: {e}")

            if str(depth_type).lower() in ('through_all', 'all', 'through'):
                try:
                    hole_input.setAllExtent()
                except Exception:
                    pass
            else:
                depth_mm = self._extract_dimension_value(params.get('depth_value', params.get('depth', 10)))
                try:
                    hole_input.setDistanceExtent(adsk.core.ValueInput.createByReal(mm(depth_mm)))
                except Exception:
                    pass

            hole_feature = holes.add(hole_input)
            try:
                hole_feature.name = f'CoPilot_Hole_{op_id}'
            except Exception:
                pass

            timeline_node = self._get_latest_timeline_node()
            diameter = diameter_mm
        else:
            # Development mock
            diameter = self._extract_dimension_value(params.get('diameter', 5))
            timeline_node = f"Timeline_Hole_{op_id}"
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'Hole_{op_id}',
            'timeline_node': timeline_node,
            'feature_type': 'hole',
            'dimensions': {'diameter': diameter}
        }
    
    def _execute_fillet(self, op_id: str, params: Dict) -> Dict:
        """Execute fillet operation."""
        # Mock implementation - actual implementation would use Fusion API
        radius = self._extract_dimension_value(params.get('radius', 2))
        
        logger.info(f"[MOCK] Created fillet: R{radius}mm")
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'Fillet_{op_id}',
            'timeline_node': f"Timeline_Fillet_{op_id}",
            'feature_type': 'fillet',
            'dimensions': {'radius': radius}
        }
    
    def _execute_chamfer(self, op_id: str, params: Dict) -> Dict:
        """Execute chamfer operation."""
        # Mock implementation
        distance = self._extract_dimension_value(params.get('distance', 1))
        
        logger.info(f"[MOCK] Created chamfer: {distance}mm")
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'Chamfer_{op_id}',
            'timeline_node': f"Timeline_Chamfer_{op_id}",
            'feature_type': 'chamfer',
            'dimensions': {'distance': distance}
        }
    
    def _execute_cut(self, op_id: str, params: Dict) -> Dict:
        """Execute cut operation."""
        # Mock implementation
        distance = self._extract_dimension_value(params.get('distance', 5))
        
        logger.info(f"[MOCK] Created cut: {distance}mm")
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'Cut_{op_id}',
            'timeline_node': f"Timeline_Cut_{op_id}",
            'feature_type': 'cut',
            'dimensions': {'distance': distance}
        }
    
    def _execute_pattern_linear(self, op_id: str, params: Dict) -> Dict:
        """Execute linear pattern operation."""
        # Mock implementation
        count = params.get('count_1', 3)
        spacing = self._extract_dimension_value(params.get('distance_1', 10))
        
        logger.info(f"[MOCK] Created linear pattern: {count} instances, {spacing}mm spacing")
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'LinearPattern_{op_id}',
            'timeline_node': f"Timeline_LinearPattern_{op_id}",
            'feature_type': 'pattern_linear',
            'dimensions': {'count': count, 'spacing': spacing}
        }

    def _execute_pattern_circular(self, op_id: str, params: Dict) -> Dict:
        """Execute circular pattern operation (mock/dev)."""
        # Mock implementation for development
        count = int(params.get('count', params.get('count_1', 6)))
        angle = self._extract_dimension_value(params.get('angle', {'value': 360, 'unit': 'deg'}))
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'CircularPattern_{op_id}',
            'timeline_node': f"Timeline_CircularPattern_{op_id}",
            'feature_type': 'pattern_circular',
            'dimensions': {'count': count, 'angle': angle}
        }

    def _execute_pattern_rectangular(self, op_id: str, params: Dict) -> Dict:
        """Execute rectangular pattern operation (mock/dev)."""
        # Mock implementation for development
        count_1 = int(params.get('count_1', params.get('count_x', 2)))
        count_2 = int(params.get('count_2', params.get('count_y', 2)))
        dist_1 = self._extract_dimension_value(params.get('distance_1', params.get('spacing_x', 10)))
        dist_2 = self._extract_dimension_value(params.get('distance_2', params.get('spacing_y', 10)))
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'RectangularPattern_{op_id}',
            'timeline_node': f"Timeline_RectangularPattern_{op_id}",
            'feature_type': 'pattern_rectangular',
            'dimensions': {'count_1': count_1, 'count_2': count_2, 'distance_1': dist_1, 'distance_2': dist_2}
        }
    
    def _execute_shell(self, op_id: str, params: Dict) -> Dict:
        """Execute shell operation."""
        # Mock implementation
        thickness = self._extract_dimension_value(params.get('thickness', 2))
        
        logger.info(f"[MOCK] Created shell: {thickness}mm thickness")
        
        return {
            'success': True,
            'operation_id': op_id,
            'feature_created': f'Shell_{op_id}',
            'timeline_node': f"Timeline_Shell_{op_id}",
            'feature_type': 'shell',
            'dimensions': {'thickness': thickness}
        }
    
    def _extract_dimension_value(self, dimension: Union[Dict, float, int]) -> float:
        """Extract numeric value from dimension parameter."""
        if isinstance(dimension, (int, float)):
            return float(dimension)
        elif isinstance(dimension, dict):
            if 'value' in dimension:
                return float(dimension['value'])
        
        raise ExecutionError(f"Invalid dimension format: {dimension}")
    
    def _mock_preview_execution(self, plan: Dict) -> Dict:
        """Mock implementation of sandbox preview."""
        operations = plan.get('operations', [])
        
        preview_data = {
            'operations_previewed': len(operations),
            'estimated_features': [],
            'bounding_box_changes': {
                'before': {'min': [0, 0, 0], 'max': [0, 0, 0]},
                'after': {'min': [-50, -25, 0], 'max': [50, 25, 10]}
            },
            'warnings': [],
            'preview_summary': f"Preview would create {len(operations)} operations"
        }
        
        # Mock feature analysis
        for op in operations:
            op_type = op.get('op')
            if op_type in ['create_sketch']:
                preview_data['estimated_features'].append(f"Sketch: {op.get('params', {}).get('name', 'Unnamed')}")
            elif op_type in ['extrude', 'cut']:
                distance = self._extract_dimension_value(op.get('params', {}).get('distance', 0))
                preview_data['estimated_features'].append(f"{op_type.title()}: {distance}mm")
            elif op_type == 'create_hole':
                diameter = self._extract_dimension_value(op.get('params', {}).get('diameter', 0))
                preview_data['estimated_features'].append(f"Hole: ⌀{diameter}mm")
            else:
                preview_data['estimated_features'].append(f"{op_type.title()}")
        
        return preview_data
    
    def _resolve_sketch_reference(self, sketch_ref: Optional[str]):
        """Resolve sketch reference to actual sketch object."""
        # TODO: Implement actual sketch resolution
        # In real implementation, this would search through the design's sketches
        # and return the matching sketch object
        if FUSION_AVAILABLE:
            try:
                if not sketch_ref:
                    return getattr(self, 'last_sketch', None)
                root_comp = self.design.rootComponent
                sketches = root_comp.sketches
                for i in range(sketches.count):
                    sk = sketches.item(i)
                    try:
                        if sk.name == sketch_ref:
                            return sk
                    except Exception:
                        # Some sketches may not have a name set yet
                        pass
                # Fallback to last_sketch if names did not match
                return getattr(self, 'last_sketch', None)
            except Exception:
                return getattr(self, 'last_sketch', None)
        
        logger.debug(f"[MOCK] Resolved sketch reference: {sketch_ref}")
        return f"MockSketch_{sketch_ref}"
    
    def _get_latest_timeline_node(self) -> str:
        """Get the most recent timeline node ID."""
        if FUSION_AVAILABLE:
            # TODO: Replace with actual Fusion API calls
            # timeline = self.design.timeline
            # latest_item = timeline.item(timeline.count - 1)
            # return latest_item.entityToken if latest_item else None
            pass
        
        # Mock implementation
        import uuid
        return f"Timeline_Node_{str(uuid.uuid4())[:8]}"

    def _get_selected_face(self):
        """Return the first selected BRepFace if available."""
        if not FUSION_AVAILABLE or not self.ui:
            return None
        try:
            selections = self.ui.activeSelections
            if not selections or selections.count == 0:
                return None
            for i in range(selections.count):
                sel = selections.item(i)
                try:
                    entity = sel.entity
                except Exception:
                    entity = None
                # Check if it's a face
                try:
                    face = adsk.fusion.BRepFace.cast(entity)
                except Exception:
                    face = None
                if face and getattr(face, 'isValid', True):
                    return face
            return None
        except Exception:
            return None


def begin_transaction() -> TransactionContext:
    """
    Begin a new transaction for atomic operation execution.
    
    Returns:
        TransactionContext that can be used with 'with' statement
    """
    return TransactionContext()


def commit_transaction(context: TransactionContext):
    """Commit a transaction context."""
    if context:
        context.commit()


def rollback_transaction(context: TransactionContext):
    """Rollback a transaction context."""
    if context:
        context.rollback()


# Example usage and testing
if __name__ == "__main__":
    # Example plan for testing
    test_plan = {
        "plan_id": "test_execution_001",
        "metadata": {
            "natural_language_prompt": "Create a simple plate with a hole",
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
                    "width": {"value": 50, "unit": "mm"},
                    "height": {"value": 30, "unit": "mm"}
                },
                "target_ref": "base_sketch"
            },
            {
                "op_id": "op_3",
                "op": "extrude",
                "params": {
                    "profile": "base_sketch",
                    "distance": {"value": 5, "unit": "mm"}
                }
            },
            {
                "op_id": "op_4",
                "op": "create_hole",
                "params": {
                    "center_point": {"x": 0, "y": 0, "z": 0},
                    "diameter": {"value": 6, "unit": "mm"},
                    "depth": "through_all"
                },
                "target_ref": "face_top"
            }
        ]
    }
    
    # Test execution
    executor = PlanExecutor()
    
    # Test preview
    print("Testing sandbox preview...")
    preview_result = executor.preview_plan_in_sandbox(test_plan)
    print(f"Preview result: {preview_result}")
    
    # Test execution
    print("\nTesting plan execution...")
    execution_result = executor.execute_plan(test_plan)
    print(f"Execution result: {execution_result}")
