"""
Fusion 360 Co-Pilot - Environment Configuration

This module handles environment variable configuration for secure API key management
and deployment-specific settings. Supports .env files and system environment variables.

Author: Fusion CoPilot Team
License: MIT
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """Manages environment variable configuration."""
    
    def __init__(self, addon_dir: Optional[str] = None):
        """Initialize environment configuration."""
        self.addon_dir = Path(addon_dir) if addon_dir else Path(__file__).parent
        self.env_file = self.addon_dir / '.env'
        self.env_vars = {}
        
        # Load environment variables
        self._load_system_env()
        self._load_env_file()
    
    def _load_system_env(self):
        """Load relevant environment variables from system."""
        env_keys = [
            # LLM API Keys
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY', 
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_ENDPOINT',
            
            # LLM Configuration
            'COPILOT_LLM_PROVIDER',
            'COPILOT_LLM_MODEL',
            'COPILOT_LLM_ENDPOINT',
            'COPILOT_LLM_TEMPERATURE',
            'COPILOT_LLM_MAX_TOKENS',
            
            # Security
            'COPILOT_ENCRYPT_LOGS',
            'COPILOT_MAX_PROMPT_LENGTH',
            
            # Performance
            'COPILOT_REQUEST_TIMEOUT',
            'COPILOT_MAX_RETRIES',
            'COPILOT_BATCH_SIZE',
            
            # Logging
            'COPILOT_LOG_LEVEL',
            'COPILOT_DEBUG_MODE',
            
            # Deployment
            'COPILOT_ENVIRONMENT',  # dev, staging, prod
            'COPILOT_INSTANCE_ID',
        ]
        
        for key in env_keys:
            value = os.getenv(key)
            if value is not None:
                self.env_vars[key] = value
                logger.debug(f"Loaded environment variable: {key}")
    
    def _load_env_file(self):
        """Load environment variables from .env file if it exists."""
        if not self.env_file.exists():
            logger.debug(f"No .env file found at {self.env_file}")
            return
        
        try:
            with open(self.env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value
                    if '=' not in line:
                        logger.warning(f"Invalid line in .env file (line {line_num}): {line}")
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Don't override system environment variables
                    if key not in self.env_vars:
                        self.env_vars[key] = value
                        logger.debug(f"Loaded from .env file: {key}")
            
            logger.info(f"Loaded {len([k for k in self.env_vars if k not in os.environ])} variables from .env file")
            
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get environment variable with type conversion."""
        value = self.env_vars.get(key, default)
        
        if value is None:
            return default
        
        # Convert string values to appropriate types
        if isinstance(value, str):
            # Boolean conversion
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            
            # Integer conversion
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                return int(value)
            
            # Float conversion
            try:
                if '.' in value:
                    return float(value)
            except ValueError:
                pass
        
        return value
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specific LLM provider."""
        key_mappings = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'azure_openai': 'AZURE_OPENAI_API_KEY'
        }
        
        key = key_mappings.get(provider.lower())
        if not key:
            logger.warning(f"Unknown provider for API key: {provider}")
            return None
        
        api_key = self.get(key)
        if not api_key:
            logger.warning(f"No API key found for {provider} (expected: {key})")
        
        return api_key
    
    def merge_with_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment variables with settings, environment takes precedence."""
        merged = settings.copy()
        
        # LLM configuration overrides
        if 'llm' not in merged:
            merged['llm'] = {}
        
        llm_config = merged['llm']
        
        if self.get('COPILOT_LLM_PROVIDER'):
            llm_config['provider'] = self.get('COPILOT_LLM_PROVIDER')
        
        if self.get('COPILOT_LLM_ENDPOINT'):
            llm_config['endpoint'] = self.get('COPILOT_LLM_ENDPOINT')
        
        if self.get('COPILOT_LLM_MODEL'):
            llm_config['model'] = self.get('COPILOT_LLM_MODEL')
        
        if self.get('COPILOT_LLM_TEMPERATURE') is not None:
            llm_config['temperature'] = self.get('COPILOT_LLM_TEMPERATURE')
        
        if self.get('COPILOT_LLM_MAX_TOKENS'):
            llm_config['max_tokens'] = self.get('COPILOT_LLM_MAX_TOKENS')
        
        if self.get('COPILOT_REQUEST_TIMEOUT'):
            llm_config['timeout'] = self.get('COPILOT_REQUEST_TIMEOUT')
        
        if self.get('COPILOT_MAX_RETRIES'):
            llm_config['max_retries'] = self.get('COPILOT_MAX_RETRIES')
        
        # API key handling - don't store in merged config for security
        provider = llm_config.get('provider', 'openai')
        api_key = self.get_api_key(provider)
        if api_key:
            llm_config['api_key'] = api_key
        
        # Performance overrides
        if 'performance' not in merged:
            merged['performance'] = {}
        
        if self.get('COPILOT_BATCH_SIZE'):
            merged['performance']['max_batch_size'] = self.get('COPILOT_BATCH_SIZE')
        
        # Security overrides
        if 'security' not in merged:
            merged['security'] = {}
        
        if self.get('COPILOT_ENCRYPT_LOGS') is not None:
            merged['security']['encrypt_logs'] = self.get('COPILOT_ENCRYPT_LOGS')
        
        if self.get('COPILOT_MAX_PROMPT_LENGTH'):
            merged['security']['max_prompt_length'] = self.get('COPILOT_MAX_PROMPT_LENGTH')
        
        # Logging overrides
        if 'logging' not in merged:
            merged['logging'] = {}
        
        if self.get('COPILOT_LOG_LEVEL'):
            merged['logging']['level'] = self.get('COPILOT_LOG_LEVEL')
        
        if self.get('COPILOT_DEBUG_MODE') is not None:
            merged['logging']['debug'] = self.get('COPILOT_DEBUG_MODE')
        
        # Advanced overrides
        if 'advanced' not in merged:
            merged['advanced'] = {}
        
        if self.get('COPILOT_ENVIRONMENT'):
            merged['advanced']['environment'] = self.get('COPILOT_ENVIRONMENT')
            
            # Set development mode based on environment
            if self.get('COPILOT_ENVIRONMENT') == 'dev':
                merged['advanced']['development_mode'] = True
        
        if self.get('COPILOT_INSTANCE_ID'):
            merged['advanced']['instance_id'] = self.get('COPILOT_INSTANCE_ID')
        
        return merged
    
    def create_env_template(self, output_file: Optional[str] = None):
        """Create a .env template file with all supported variables."""
        if output_file is None:
            output_file = str(self.addon_dir / '.env.template')
        
        template_content = """# Fusion 360 Co-Pilot Environment Configuration
# Copy this file to .env and fill in your values
# Never commit .env files with real API keys to version control!

# ============================================================================
# LLM API KEYS (REQUIRED FOR PRODUCTION)
# ============================================================================

# OpenAI API Key (for GPT models)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (for Claude models) 
# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Azure OpenAI (for enterprise deployments)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Primary LLM provider (openai, anthropic, azure_openai)
COPILOT_LLM_PROVIDER=openai

# Model to use
COPILOT_LLM_MODEL=gpt-4

# Custom endpoint (optional - will use provider defaults if not set)
# COPILOT_LLM_ENDPOINT=https://api.openai.com/v1/chat/completions

# Creativity/randomness (0.0 = deterministic, 1.0 = creative)
COPILOT_LLM_TEMPERATURE=0.2

# Maximum response tokens
COPILOT_LLM_MAX_TOKENS=2000

# ============================================================================
# PERFORMANCE & RELIABILITY
# ============================================================================

# Request timeout in seconds
COPILOT_REQUEST_TIMEOUT=30

# Maximum retry attempts for failed requests
COPILOT_MAX_RETRIES=3

# Operations per batch for performance
COPILOT_BATCH_SIZE=10

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

# Encrypt sensitive data in logs (true/false)
COPILOT_ENCRYPT_LOGS=false

# Maximum allowed prompt length (characters)
COPILOT_MAX_PROMPT_LENGTH=2000

# ============================================================================
# LOGGING & DEBUGGING
# ============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
COPILOT_LOG_LEVEL=INFO

# Enable debug mode with detailed logging (true/false)
COPILOT_DEBUG_MODE=false

# ============================================================================
# DEPLOYMENT SETTINGS
# ============================================================================

# Environment (dev, staging, prod)
COPILOT_ENVIRONMENT=prod

# Unique instance identifier (for multi-instance deployments)
COPILOT_INSTANCE_ID=copilot-001

# ============================================================================
# NOTES
# ============================================================================
# 
# Environment variables take precedence over settings.yaml values
# This allows for secure deployment without modifying config files
# 
# For security:
# - Never commit .env files to version control
# - Use different API keys for dev/staging/prod
# - Rotate API keys regularly
# - Monitor API usage and costs
# 
# For development:
# - Use COPILOT_ENVIRONMENT=dev for additional debugging
# - Set COPILOT_DEBUG_MODE=true for verbose logging
# - Test with different models and temperatures
#
"""
        
        try:
            with open(output_file, 'w') as f:
                f.write(template_content)
            logger.info(f"Created environment template: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Failed to create environment template: {e}")
            return None
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration and return status."""
        status = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'api_keys_found': {},
            'environment': self.get('COPILOT_ENVIRONMENT', 'unknown')
        }
        
        # Check for API keys
        providers = ['openai', 'anthropic', 'azure_openai']
        for provider in providers:
            api_key = self.get_api_key(provider)
            status['api_keys_found'][provider] = bool(api_key)
            
            if api_key and len(api_key) < 10:
                status['warnings'].append(f"{provider} API key seems too short")
        
        # Check if no API keys are configured
        if not any(status['api_keys_found'].values()):
            status['errors'].append("No API keys found - production mode requires at least one API key")
            status['valid'] = False
        
        # Validate numeric settings
        numeric_checks = [
            ('COPILOT_REQUEST_TIMEOUT', 1, 300, "Request timeout should be 1-300 seconds"),
            ('COPILOT_MAX_RETRIES', 0, 10, "Max retries should be 0-10"),
            ('COPILOT_LLM_MAX_TOKENS', 100, 4000, "Max tokens should be 100-4000"),
            ('COPILOT_MAX_PROMPT_LENGTH', 100, 10000, "Max prompt length should be 100-10000 characters")
        ]
        
        for key, min_val, max_val, message in numeric_checks:
            value = self.get(key)
            if value is not None:
                try:
                    num_val = float(value)
                    if not (min_val <= num_val <= max_val):
                        status['warnings'].append(f"{key}: {message}")
                except (ValueError, TypeError):
                    status['warnings'].append(f"{key}: Must be a number")
        
        # Check environment consistency
        environment = self.get('COPILOT_ENVIRONMENT', 'unknown')
        if environment == 'prod' and not any(status['api_keys_found'].values()):
            status['errors'].append("Production environment requires valid API keys")
            status['valid'] = False
        
        return status


# Global instance for easy access
_env_config = None

def get_environment_config(addon_dir: Optional[str] = None) -> EnvironmentConfig:
    """Get or create the global environment configuration instance."""
    global _env_config
    if _env_config is None:
        _env_config = EnvironmentConfig(addon_dir)
    return _env_config


def load_settings_with_env(settings_dict: Dict[str, Any], addon_dir: Optional[str] = None) -> Dict[str, Any]:
    """Load settings merged with environment configuration."""
    env_config = get_environment_config(addon_dir)
    return env_config.merge_with_settings(settings_dict)