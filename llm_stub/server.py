#!/usr/bin/env python3
"""
Fusion 360 Co-Pilot - LLM Stub Server

A lightweight local server that provides canned responses for development and testing
without requiring external LLM API keys or network connectivity.

Usage:
    python server.py [--port 8080] [--host localhost]

Author: Fusion CoPilot Team
License: MIT
"""

import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

try:
    from flask import Flask, request, jsonify, Response
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    print("Flask not available. Install with: pip install flask flask-cors")
    FLASK_AVAILABLE = False
    Flask = None
    CORS = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
app = None
canned_plans = {}


def create_app():
    """Create and configure the Flask application."""
    global app, canned_plans
    
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required but not available")
    
    app = Flask(__name__)
    CORS(app)  # Enable CORS for cross-origin requests
    
    # Load canned responses
    canned_plans = load_canned_plans()
    logger.info(f"Loaded {len(canned_plans)} canned plan responses")
    
    @app.route('/', methods=['GET'])
    def index():
        """Health check and info endpoint."""
        return jsonify({
            'service': 'Fusion 360 Co-Pilot LLM Stub',
            'version': '1.0.0',
            'status': 'running',
            'available_plans': len(canned_plans),
            'endpoints': {
                '/llm': 'POST - Main LLM endpoint for plan generation',
                '/health': 'GET - Health check',
                '/plans': 'GET - List available canned plans',
                '/plans/<plan_id>': 'GET - Get specific canned plan'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    @app.route('/health', methods=['GET'])
    def health():
        """Simple health check endpoint."""
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat() + 'Z'})
    
    @app.route('/llm', methods=['POST'])
    def llm_endpoint():
        """
        Main LLM endpoint that mimics a real LLM service.
        
        Accepts natural language prompts and returns structured plans.
        """
        try:
            # Parse request
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            prompt = data.get('prompt', '').strip()
            context = data.get('context', {})
            
            if not prompt:
                return jsonify({'error': 'Prompt is required'}), 400
            
            logger.info(f"Received prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # Find matching canned response
            plan = find_matching_plan(prompt, context)
            
            if not plan:
                # Generate a generic "unknown" response
                plan = generate_fallback_plan(prompt, context)
            
            # Add response metadata
            response = {
                'plan_id': plan.get('plan_id'),
                'metadata': plan.get('metadata', {}),
                'operations': plan.get('operations', []),
                'response_metadata': {
                    'source': 'llm_stub',
                    'processing_time_ms': 250,  # Simulate processing time
                    'model': 'canned_responses_v1.0',
                    'confidence': 0.85,
                    'matched_pattern': get_matched_pattern(prompt)
                }
            }
            
            # Update metadata with current timestamp
            response['metadata']['created_at'] = datetime.utcnow().isoformat() + 'Z'
            response['metadata']['natural_language_prompt'] = prompt
            
            logger.info(f"Returning plan: {plan.get('plan_id')} with {len(plan.get('operations', []))} operations")
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error processing LLM request: {e}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    
    @app.route('/plans', methods=['GET'])
    def list_plans():
        """List all available canned plans."""
        plan_list = []
        for plan_id, plan in canned_plans.items():
            plan_list.append({
                'plan_id': plan_id,
                'prompt_pattern': plan.get('prompt_pattern', ''),
                'description': plan.get('description', ''),
                'operations_count': len(plan.get('operations', [])),
                'difficulty': plan.get('difficulty', 'unknown')
            })
        
        return jsonify({
            'total_plans': len(plan_list),
            'plans': plan_list
        })
    
    @app.route('/plans/<plan_id>', methods=['GET'])
    def get_plan(plan_id):
        """Get a specific canned plan by ID."""
        if plan_id not in canned_plans:
            return jsonify({'error': f'Plan not found: {plan_id}'}), 404
        
        return jsonify(canned_plans[plan_id])
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


def load_canned_plans() -> Dict:
    """Load canned plan responses from JSON file."""
    current_dir = Path(__file__).parent
    canned_file = current_dir / 'canned_plans.json'
    
    try:
        if canned_file.exists():
            with open(canned_file, 'r') as f:
                data = json.load(f)
                return data.get('plans', {})
        else:
            logger.warning(f"Canned plans file not found: {canned_file}")
            return generate_default_canned_plans()
            
    except Exception as e:
        logger.error(f"Failed to load canned plans: {e}")
        return generate_default_canned_plans()


def generate_default_canned_plans() -> Dict:
    """Generate default canned plans if file is not available."""
    return {
        'simple_plate': {
            'plan_id': 'simple_plate_001',
            'prompt_pattern': 'rectangular plate',
            'description': 'Simple rectangular plate extrusion',
            'difficulty': 'beginner',
            'metadata': {
                'estimated_duration_seconds': 15,
                'confidence_score': 0.95,
                'units': 'mm'
            },
            'operations': [
                {
                    'op_id': 'op_1',
                    'op': 'create_sketch',
                    'params': {
                        'plane': 'XY',
                        'name': 'base_sketch'
                    }
                },
                {
                    'op_id': 'op_2',
                    'op': 'draw_rectangle',
                    'params': {
                        'center_point': {'x': 0, 'y': 0, 'z': 0},
                        'width': {'value': 100, 'unit': 'mm'},
                        'height': {'value': 50, 'unit': 'mm'}
                    },
                    'target_ref': 'base_sketch',
                    'dependencies': ['op_1']
                },
                {
                    'op_id': 'op_3',
                    'op': 'extrude',
                    'params': {
                        'profile': 'base_sketch',
                        'distance': {'value': 5, 'unit': 'mm'},
                        'direction': 'positive',
                        'operation': 'new_body'
                    },
                    'dependencies': ['op_2']
                }
            ]
        }
    }


def find_matching_plan(prompt: str, context: Dict) -> Optional[Dict]:
    """Find the best matching canned plan for a given prompt."""
    prompt_lower = prompt.lower()
    
    # Simple keyword matching - in a real implementation, this would be more sophisticated
    for plan_id, plan in canned_plans.items():
        pattern = plan.get('prompt_pattern', '').lower()
        keywords = plan.get('keywords', [])
        
        # Check if pattern matches
        if pattern and pattern in prompt_lower:
            return plan.copy()
        
        # Check keywords
        if keywords and any(keyword.lower() in prompt_lower for keyword in keywords):
            return plan.copy()
    
    return None


def get_matched_pattern(prompt: str) -> str:
    """Get the pattern that matched the prompt."""
    prompt_lower = prompt.lower()
    
    for plan_id, plan in canned_plans.items():
        pattern = plan.get('prompt_pattern', '').lower()
        if pattern and pattern in prompt_lower:
            return pattern
    
    return 'fallback'


def generate_fallback_plan(prompt: str, context: Dict) -> Dict:
    """Generate a fallback plan for unrecognized prompts."""
    return {
        'plan_id': 'fallback_unknown',
        'metadata': {
            'estimated_duration_seconds': 30,
            'confidence_score': 0.3,
            'units': context.get('units', 'mm'),
            'requires_user_input': True,
            'clarification_questions': [
                'Could you be more specific about the dimensions?',
                'What type of geometry would you like to create?',
                'Are you trying to create, modify, or analyze something?'
            ]
        },
        'operations': [
            {
                'op_id': 'op_1',
                'op': 'create_sketch',
                'params': {
                    'plane': 'XY',
                    'name': 'sketch_placeholder'
                }
            }
        ]
    }


def main():
    """Main entry point for the stub server."""
    parser = argparse.ArgumentParser(description='Fusion 360 Co-Pilot LLM Stub Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run server on')
    parser.add_argument('--host', default='localhost', help='Host to bind server to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if not FLASK_AVAILABLE:
        print("Error: Flask is required but not installed.")
        print("Install with: pip install flask flask-cors")
        return 1
    
    try:
        # Create Flask app
        app = create_app()
        
        # Start server
        logger.info(f"Starting Fusion 360 Co-Pilot LLM Stub Server")
        logger.info(f"Server will be available at: http://{args.host}:{args.port}")
        logger.info(f"Main endpoint: http://{args.host}:{args.port}/llm")
        logger.info(f"Press Ctrl+C to stop the server")
        
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=False  # Disable reloader to avoid duplicate startup messages
        )
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
