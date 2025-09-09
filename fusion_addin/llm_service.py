"""
Fusion 360 Co-Pilot - Production LLM Service

This module provides production-ready LLM integration supporting multiple providers
(OpenAI, Anthropic, Azure OpenAI) with comprehensive error handling, retries, and
structured plan generation.

Author: Fusion CoPilot Team
License: MIT
"""

import json
import logging
import time
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

try:
    import requests
    REQUESTS_AVAILABLE = True
    RequestsResponse = requests.Response
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None
    # Create a dummy class for type hints
    class RequestsResponse:
        pass
    requests = None

# Configure logging
logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


@dataclass
class LLMConfig:
    """Configuration for LLM service."""
    provider: LLMProvider
    endpoint: str
    api_key: str
    model: str
    max_tokens: int = 2000
    temperature: float = 0.2
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    plan_id: str
    metadata: Dict[str, Any]
    operations: List[Dict[str, Any]]
    response_metadata: Dict[str, Any]
    raw_response: Optional[str] = None
    error: Optional[str] = None


class LLMService:
    """Production LLM service with multi-provider support."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM service with configuration."""
        self.config = config
        self.session = None
        
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library is required for LLM service")
        
        # Initialize HTTP session
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
        else:
            self.session = None
        self._setup_authentication()
        
        logger.info(f"Initialized LLM service: {config.provider.value} - {config.model}")
    
    def _setup_authentication(self):
        """Setup authentication headers for the selected provider."""
        if self.config.provider == LLMProvider.OPENAI:
            self.session.headers.update({
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json'
            })
        elif self.config.provider == LLMProvider.ANTHROPIC:
            self.session.headers.update({
                'x-api-key': self.config.api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            })
        elif self.config.provider == LLMProvider.AZURE_OPENAI:
            self.session.headers.update({
                'api-key': self.config.api_key,
                'Content-Type': 'application/json'
            })
    
    def generate_plan(self, prompt: str, context: Optional[Dict] = None) -> LLMResponse:
        """
        Generate a structured CAD plan from natural language prompt.
        
        Args:
            prompt: Natural language description of CAD operations
            context: Additional context (units, constraints, etc.)
            
        Returns:
            LLMResponse with structured plan or error information
        """
        context = context or {}
        start_time = time.time()
        
        try:
            # Build system message for CAD context
            system_message = self._build_system_message(context)
            
            # Format request for specific provider
            request_data = self._format_request(prompt, system_message)
            
            # Send request with retry logic
            response = self._send_request_with_retry(request_data)
            
            if not response:
                return LLMResponse(
                    plan_id="error_no_response",
                    metadata={},
                    operations=[],
                    response_metadata={},
                    error="Failed to get response from LLM provider"
                )
            
            # Parse and validate response
            llm_response = self._parse_response(response, prompt)
            
            # Add timing metadata
            processing_time = (time.time() - start_time) * 1000
            llm_response.response_metadata['processing_time_ms'] = processing_time
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return LLMResponse(
                plan_id="error_exception",
                metadata={},
                operations=[],
                response_metadata={},
                error=str(e)
            )
    
    def _build_system_message(self, context: Dict) -> str:
        """Build system message with CAD-specific context."""
        units = context.get('units', 'mm')
        max_operations = context.get('max_operations', 50)
        
        return f"""You are a Fusion 360 CAD expert assistant. Convert natural language descriptions 
into precise, structured JSON plans following this schema:

{{
    "plan_id": "unique_identifier",
    "metadata": {{
        "estimated_duration_seconds": 30,
        "confidence_score": 0.95,
        "units": "{units}",
        "created_at": "ISO timestamp",
        "natural_language_prompt": "original prompt"
    }},
    "operations": [
        {{
            "op_id": "unique_operation_id",
            "op": "operation_type",
            "params": {{
                "parameter_name": {{"value": 100, "unit": "{units}"}}
            }},
            "target_ref": "reference_to_other_operation",
            "dependencies": ["list_of_dependency_op_ids"]
        }}
    ]
}}

Key guidelines:
1. Use {units} as the primary unit unless specified otherwise
2. Maximum {max_operations} operations per plan
3. Include proper dependencies between operations
4. Validate geometric feasibility
5. Use precise parameter names and values
6. If ambiguous, ask clarifying questions

Supported operations: create_sketch, draw_rectangle, draw_circle, draw_line, draw_arc, 
draw_polygon, extrude, cut, revolve, sweep, loft, hole_simple, hole_countersink, 
hole_counterbore, hole_threaded, fillet, chamfer, shell, mirror, pattern_linear, 
pattern_circular, create_plane, create_axis, create_point, create_component, 
create_joint, add_dimension, add_constraint, rename.

Return ONLY the JSON plan, no additional text."""
    
    def _format_request(self, prompt: str, system_message: str) -> Dict:
        """Format request for specific LLM provider."""
        if self.config.provider == LLMProvider.OPENAI:
            return {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
        
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "system": system_message,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        
        elif self.config.provider == LLMProvider.AZURE_OPENAI:
            return {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
    
    def _send_request_with_retry(self, request_data: Dict) -> Optional[RequestsResponse]:
        """Send request with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Sending LLM request (attempt {attempt + 1}/{self.config.max_retries})")
                
                response = self.session.post(
                    self.config.endpoint,
                    json=request_data,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get('retry-after', self.config.retry_delay))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue
                elif response.status_code in [500, 502, 503, 504]:  # Server errors
                    logger.warning(f"Server error {response.status_code}, retrying...")
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"LLM request failed: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:  # Handle both requests exceptions and other errors
                last_exception = e
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
        
        logger.error(f"All retry attempts failed. Last error: {last_exception}")
        return None
    
    def _parse_response(self, response: RequestsResponse, original_prompt: str) -> LLMResponse:
        """Parse LLM response into standardized format."""
        try:
            response_data = response.json()
            
            # Extract content based on provider
            if self.config.provider == LLMProvider.OPENAI:
                content = response_data['choices'][0]['message']['content']
                usage = response_data.get('usage', {})
            elif self.config.provider == LLMProvider.ANTHROPIC:
                content = response_data['content'][0]['text']
                usage = response_data.get('usage', {})
            elif self.config.provider == LLMProvider.AZURE_OPENAI:
                content = response_data['choices'][0]['message']['content']
                usage = response_data.get('usage', {})
            else:
                raise ValueError(f"Unknown provider: {self.config.provider}")
            
            # Parse JSON plan from content
            try:
                # Clean content (remove markdown code blocks if present)
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                
                plan = json.loads(content.strip())
                
                # Validate required fields
                if 'plan_id' not in plan:
                    plan['plan_id'] = f"generated_{int(time.time())}"
                if 'metadata' not in plan:
                    plan['metadata'] = {}
                if 'operations' not in plan:
                    plan['operations'] = []
                
                # Add metadata
                plan['metadata']['created_at'] = datetime.utcnow().isoformat() + 'Z'
                plan['metadata']['natural_language_prompt'] = original_prompt
                
                return LLMResponse(
                    plan_id=plan['plan_id'],
                    metadata=plan['metadata'],
                    operations=plan['operations'],
                    response_metadata={
                        'provider': self.config.provider.value,
                        'model': self.config.model,
                        'usage': usage,
                        'raw_response': content
                    },
                    raw_response=content
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                logger.debug(f"Raw content: {content}")
                return LLMResponse(
                    plan_id="error_json_parse",
                    metadata={},
                    operations=[],
                    response_metadata={},
                    error=f"Invalid JSON response: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return LLMResponse(
                plan_id="error_response_parse",
                metadata={},
                operations=[],
                response_metadata={},
                error=str(e)
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on LLM service."""
        try:
            # Simple test request
            test_response = self.generate_plan("Create a simple 10mm cube", {"units": "mm"})
            
            return {
                'status': 'healthy' if not test_response.error else 'unhealthy',
                'provider': self.config.provider.value,
                'model': self.config.model,
                'endpoint': self.config.endpoint,
                'error': test_response.error,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': self.config.provider.value,
                'model': self.config.model,
                'endpoint': self.config.endpoint,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }


def create_llm_service(settings: Dict) -> LLMService:
    """Factory function to create LLM service from settings."""
    llm_config = settings.get('llm', {})
    
    # Determine provider from endpoint or explicit config
    provider_name = llm_config.get('provider', 'openai').lower()
    endpoint = llm_config.get('endpoint', '')
    
    if 'openai' in endpoint and 'azure' not in endpoint:
        provider = LLMProvider.OPENAI
        if not endpoint.endswith('/chat/completions'):
            endpoint = 'https://api.openai.com/v1/chat/completions'
    elif 'anthropic' in endpoint:
        provider = LLMProvider.ANTHROPIC
        if not endpoint.endswith('/messages'):
            endpoint = 'https://api.anthropic.com/v1/messages'
    elif 'azure' in endpoint:
        provider = LLMProvider.AZURE_OPENAI
    else:
        # Default to OpenAI
        provider = LLMProvider.OPENAI
        endpoint = 'https://api.openai.com/v1/chat/completions'
    
    # Get API key from environment or settings
    api_key = (
        llm_config.get('api_key') or 
        os.getenv('OPENAI_API_KEY') or
        os.getenv('ANTHROPIC_API_KEY') or
        os.getenv('AZURE_OPENAI_API_KEY') or
        ''
    )
    
    if not api_key:
        raise ValueError(f"API key required for {provider.value}. Set in settings.yaml or environment variable.")
    
    config = LLMConfig(
        provider=provider,
        endpoint=endpoint,
        api_key=api_key,
        model=llm_config.get('model', 'gpt-4' if provider == LLMProvider.OPENAI else 'claude-3-sonnet-20240229'),
        max_tokens=llm_config.get('max_tokens', 2000),
        temperature=llm_config.get('temperature', 0.2),
        timeout=llm_config.get('timeout', 30),
        max_retries=llm_config.get('max_retries', 3),
        retry_delay=llm_config.get('retry_delay', 1.0)
    )
    
    return LLMService(config)