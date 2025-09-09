"""
Fusion 360 Natural-Language CAD Co-Pilot - Main Entry Point

This is the main entry point for the Fusion 360 add-in. It manages the add-in
lifecycle, creates UI components, and coordinates between the various modules.

Author: Fusion CoPilot Team
License: MIT
"""

import os
import sys
import json
import traceback

# Handle missing dependencies gracefully
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not available. Please install: pip3 install --break-system-packages pyyaml")
    yaml = None
from typing import Dict, Optional, Any
import logging

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Fusion 360 API imports
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

# Import our modules
try:
    from ui import CoPilotUI
    from executor import PlanExecutor
    from sanitizer import PlanSanitizer
    from action_log import ActionLogger
    from llm_service import create_llm_service, LLMService
    from env_config import load_settings_with_env, get_environment_config
except ImportError as e:
    # Handle import errors gracefully
    print(f"Import error: {e}")
    CoPilotUI = None
    PlanExecutor = None
    PlanSanitizer = None
    ActionLogger = None

# Global variables for add-in state
app: Optional[Any] = None
ui: Optional[Any] = None
copilot_ui: Optional[CoPilotUI] = None
executor: Optional[PlanExecutor] = None
sanitizer: Optional[PlanSanitizer] = None
action_logger: Optional[ActionLogger] = None
settings: Dict = {}
command_definitions: Dict = {}

# Configure logging
def setup_logging():
    """Setup logging configuration."""
    log_dir = os.path.join(current_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'copilot.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Setup logging immediately
setup_logging()
logger = logging.getLogger(__name__)


def run(context):
    """
    Entry point for the Fusion 360 add-in.
    
    This function is called by Fusion 360 when the add-in is loaded.
    
    Args:
        context: Fusion 360 add-in context
    """
    global app, ui, copilot_ui, executor, sanitizer, action_logger, settings
    
    try:
        logger.info("Starting Fusion 360 Natural-Language CAD Co-Pilot")
        print("[CoPilot] run(): entered")
        
        # Initialize Fusion API connection
        if FUSION_AVAILABLE:
            app = adsk.core.Application.get()
            ui = app.userInterface
            try:
                app.log("[CoPilot] Fusion available, UI acquired", adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                print("[CoPilot] Fusion available, UI acquired")
            
            if not app or not ui:
                raise Exception("Failed to get Fusion 360 application or UI")
        else:
            logger.info("Running in development mode (Fusion API not available)")
        
        # Load settings
        settings = load_settings()
        print("[CoPilot] Settings loaded")
        logger.info(f"Loaded settings with LLM endpoint: {settings.get('llm', {}).get('endpoint', 'unknown')}")
        
        # Initialize core components
        print("[CoPilot] Initializing components...")
        initialize_components()
        print("[CoPilot] Components initialized")
        
        # Create UI components
        print("[CoPilot] Creating UI components...")
        create_ui_components()
        print("[CoPilot] UI components created")
        
        # Register command handlers
        print("[CoPilot] Registering commands...")
        register_commands()
        print("[CoPilot] Commands registered")
        
        logger.info("Co-Pilot add-in started successfully")
        
        if FUSION_AVAILABLE and ui:
            ui.messageBox("Fusion 360 Co-Pilot loaded successfully!\n\n"
                         "Click the 'CoPilot' button in the toolbar to begin.",
                         "Co-Pilot Ready")
            try:
                app.log("[CoPilot] run(): end - success dialog shown", adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass
    
    except Exception as e:
        error_msg = f"Failed to start Co-Pilot add-in: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        if FUSION_AVAILABLE and ui:
            ui.messageBox(f"Error starting Co-Pilot:\n\n{error_msg}", 
                         "Co-Pilot Error", 
                         adsk.core.MessageBoxButtonTypes.OKButtonType,
                         adsk.core.MessageBoxIconTypes.CriticalIconType)


def stop(context):
    """
    Clean up when the add-in is stopped.
    
    Args:
        context: Fusion 360 add-in context
    """
    global app, ui, copilot_ui, executor, sanitizer, action_logger, command_definitions
    
    try:
        logger.info("Stopping Fusion 360 Natural-Language CAD Co-Pilot")
        
        # Clean up UI components
        cleanup_ui_components()
        
        # Unregister commands
        cleanup_commands()
        
        # Clean up core components
        if copilot_ui:
            copilot_ui.cleanup()
            copilot_ui = None
        
        if action_logger:
            # Save any pending logs
            action_logger.cleanup_old_logs()
            action_logger = None
        
        executor = None
        sanitizer = None
        
        logger.info("Co-Pilot add-in stopped successfully")
        
    except Exception as e:
        logger.error(f"Error stopping Co-Pilot add-in: {str(e)}")
        logger.error(traceback.format_exc())


def load_settings() -> Dict:
    """Load settings from settings.yaml file merged with environment configuration."""
    settings_file = os.path.join(current_dir, 'settings.yaml')
    
    try:
        # Load base settings from YAML
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                base_settings = yaml.safe_load(f)
                logger.info("Settings loaded from settings.yaml")
        else:
            logger.warning("settings.yaml not found, using defaults")
            base_settings = get_default_settings()
        
        # Merge with environment configuration
        final_settings = load_settings_with_env(base_settings, current_dir)
        
        # Log configuration status
        env_config = get_environment_config(current_dir)
        config_status = env_config.validate_configuration()
        
        if config_status['warnings']:
            for warning in config_status['warnings']:
                logger.warning(f"Configuration warning: {warning}")
        
        if config_status['errors']:
            for error in config_status['errors']:
                logger.error(f"Configuration error: {error}")
        
        environment = config_status.get('environment', 'unknown')
        api_keys_count = sum(1 for found in config_status['api_keys_found'].values() if found)
        logger.info(f"Configuration loaded - Environment: {environment}, API keys: {api_keys_count}")
        
        return final_settings
            
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        return get_default_settings()


def get_default_settings() -> Dict:
    """Get default settings if settings.yaml is not available."""
    return {
        'llm': {
            'endpoint': 'http://localhost:8080/llm',
            'local_mode': True,
            'timeout': 30
        },
        'processing': {
            'units_default': 'mm',
            'max_operations_per_plan': 50,
            'enable_preview': True
        },
        'ui': {
            'default_dock_position': 'right',
            'theme': 'auto'
        },
        'logging': {
            'debug': False,
            'level': 'INFO'
        }
    }


def initialize_components():
    """Initialize core Co-Pilot components."""
    global executor, sanitizer, action_logger
    
    try:
        # Initialize sanitizer with machine profile
        machine_profile = settings.get('machine_profile', {})
        sanitizer = PlanSanitizer(machine_profile, settings)
        logger.info("Plan sanitizer initialized")
        
        # Initialize executor
        executor = PlanExecutor(settings)
        logger.info("Plan executor initialized")
        
        # Initialize action logger
        log_dir = settings.get('action_log', {}).get('log_directory', 'logs/actions')
        action_logger = ActionLogger(
            os.path.join(current_dir, log_dir),
            settings.get('action_log', {})
        )
        logger.info("Action logger initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


def create_ui_components():
    """Create and register UI components."""
    global copilot_ui
    
    try:
        if FUSION_AVAILABLE and ui:
            # Initialize the Co-Pilot UI
            copilot_ui = CoPilotUI(app, ui, settings)
            copilot_ui.create_ui()
            logger.info("Co-Pilot UI created successfully")
        else:
            logger.info("UI creation skipped (development mode)")
            
    except Exception as e:
        logger.error(f"Failed to create UI components: {e}")
        raise


def register_commands():
    """Register command handlers for UI interactions."""
    global command_definitions
    
    try:
        if FUSION_AVAILABLE and ui:
            # Register main Co-Pilot command
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                'fusion_copilot_open',
                'CoPilot',
                'Open the Natural Language CAD Co-Pilot'
            )
            
            # Connect command handler
            cmd_handler = CoPilotCommandHandler()
            cmd_def.commandCreated.add(cmd_handler)
            command_definitions['copilot_open'] = cmd_def
            
            # Add to toolbar
            create_panel = ui.allToolbarPanels.itemById('SolidCreatePanel')
            if create_panel:
                create_panel.controls.addCommand(cmd_def, '', False)
                logger.info("Co-Pilot command added to toolbar")
            
        else:
            logger.info("Command registration skipped (development mode)")
            
    except Exception as e:
        logger.error(f"Failed to register commands: {e}")


def cleanup_ui_components():
    """Clean up UI components."""
    try:
        if FUSION_AVAILABLE and ui:
            # Remove from toolbar
            create_panel = ui.allToolbarPanels.itemById('SolidCreatePanel')
            if create_panel:
                copilot_control = create_panel.controls.itemById('fusion_copilot_open')
                if copilot_control:
                    copilot_control.deleteMe()
            
        logger.info("UI components cleaned up")
        
    except Exception as e:
        logger.error(f"Error cleaning up UI: {e}")


def cleanup_commands():
    """Clean up registered commands."""
    global command_definitions
    
    try:
        if FUSION_AVAILABLE and ui:
            for cmd_id, cmd_def in command_definitions.items():
                if cmd_def and cmd_def.isValid:
                    cmd_def.deleteMe()
            
            command_definitions.clear()
            logger.info("Commands cleaned up")
            
    except Exception as e:
        logger.error(f"Error cleaning up commands: {e}")


class CoPilotCommandHandler(adsk.core.CommandCreatedEventHandler if FUSION_AVAILABLE else object):
    """
    Command handler for the main Co-Pilot command.
    
    This handles the creation and execution of the Co-Pilot dialog/panel.
    """
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        """Handle command creation event."""
        try:
            if not FUSION_AVAILABLE:
                return
                
            command = args.command
            inputs = command.commandInputs
            
            # Create command inputs for the Co-Pilot dialog
            self.create_command_inputs(inputs)
            
            # Connect event handlers
            execute_handler = CoPilotExecuteHandler()
            command.execute.add(execute_handler)
            
            input_changed_handler = CoPilotInputChangedHandler()
            command.inputChanged.add(input_changed_handler)
            
        except Exception as e:
            logger.error(f"Error in command handler: {e}")
            if FUSION_AVAILABLE and ui:
                ui.messageBox(f'Command handler error: {str(e)}')
    
    def create_command_inputs(self, inputs):
        """Create the command dialog inputs."""
        try:
            # Main prompt input
            prompt_input = inputs.addTextBoxCommandInput(
                'prompt_input',
                'Natural Language Prompt',
                'Describe what you want to create...',
                5,  # Number of rows
                False  # Read only
            )
            prompt_input.tooltip = "Enter your natural language description of what you want to create"
            
            # Action buttons group
            button_group = inputs.addGroupCommandInput('action_buttons', 'Actions')
            button_group.isExpanded = True
            
            # Parse button
            # Fusion expects a RELATIVE resource folder path here
            icon_dir = 'resources/commandIcons'
            # Parse button
            parse_button = button_group.children.addBoolValueInput(
                'parse_button',
                'Parse',
                True,
                icon_dir,
                False
            )
            parse_button.tooltip = "Convert natural language to structured plan"
            
            # Preview button
            # Preview button
            preview_button = button_group.children.addBoolValueInput(
                'preview_button',
                'Preview',
                True,
                icon_dir,
                False
            )
            preview_button.tooltip = "Preview operations in sandbox mode"
            
            # Apply button
            # Apply button
            apply_button = button_group.children.addBoolValueInput(
                'apply_button',
                'Apply',
                True,
                icon_dir,
                False
            )
            apply_button.tooltip = "Apply operations to active design"
            
            # Results display
            results_input = inputs.addTextBoxCommandInput(
                'results_display',
                'Results',
                '',
                10,  # Number of rows
                True  # Read only
            )
            results_input.tooltip = "Shows parsing results and operation details"
            
        except Exception as e:
            logger.error(f"Error creating command inputs: {e}")


class CoPilotExecuteHandler(adsk.core.CommandEventHandler if FUSION_AVAILABLE else object):
    """Handler for command execution."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        """Handle command execution."""
        try:
            if not FUSION_AVAILABLE:
                return
                
            inputs = args.command.commandInputs
            
            # Get the prompt text
            prompt_input = inputs.itemById('prompt_input')
            prompt_text = prompt_input.text if prompt_input else ""
            
            if not prompt_text.strip():
                ui.messageBox("Please enter a prompt describing what you want to create.")
                return
            
            # Process the prompt
            self.process_natural_language_prompt(prompt_text, inputs)
            
        except Exception as e:
            logger.error(f"Error in execute handler: {e}")
            if FUSION_AVAILABLE and ui:
                ui.messageBox(f'Execute error: {str(e)}')
    
    def process_natural_language_prompt(self, prompt: str, inputs):
        """Process the natural language prompt through the Co-Pilot pipeline."""
        try:
            results_display = inputs.itemById('results_display')
            
            # Step 1: Send to LLM for parsing
            results_display.text = "Parsing natural language prompt..."
            
            parsed_plan = self.send_to_llm(prompt)
            
            if not parsed_plan:
                results_display.text = "Failed to parse prompt. Check LLM connection."
                return
            
            # Step 2: Sanitize the plan
            results_display.text += "\n\nValidating and sanitizing plan..."
            
            is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(parsed_plan)
            
            if not is_valid:
                results_display.text += f"\n\nValidation failed:\n" + "\n".join(messages)
                return
            
            # Step 3: Show sanitized plan
            results_display.text += f"\n\nPlan validated successfully!"
            results_display.text += f"\nOperations: {len(sanitized_plan.get('operations', []))}"
            
            if messages:
                results_display.text += f"\n\nWarnings:\n" + "\n".join(messages)
            
            # Step 4: Preview (if requested)
            # This would be handled by button clicks in a full implementation
            
            results_display.text += f"\n\nReady for preview or execution."
            
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            results_display.text = f"Error: {str(e)}"
    
    def send_to_llm(self, prompt: str) -> Optional[Dict]:
        """Send prompt to LLM and get structured plan using production LLM service."""
        try:
            llm_config = settings.get('llm', {})
            
            # Check if we should use local stub mode
            if llm_config.get('local_mode', False):
                # Fall back to simple HTTP request for stub server
                return self._send_to_stub_server(prompt)
            
            # Use production LLM service
            try:
                llm_service = create_llm_service(settings)
                
                context = {
                    'units': settings.get('processing', {}).get('units_default', 'mm'),
                    'max_operations': settings.get('processing', {}).get('max_operations_per_plan', 50)
                }
                
                response = llm_service.generate_plan(prompt, context)
                
                if response.error:
                    logger.error(f"LLM service error: {response.error}")
                    return None
                
                # Convert to expected format
                return {
                    'plan_id': response.plan_id,
                    'metadata': response.metadata,
                    'operations': response.operations,
                    'response_metadata': response.response_metadata
                }
                
            except ValueError as e:
                logger.warning(f"LLM service configuration error: {e}")
                logger.info("Falling back to stub server mode")
                return self._send_to_stub_server(prompt)
                
        except Exception as e:
            logger.error(f"LLM request error: {e}")
            return None
    
    def _send_to_stub_server(self, prompt: str) -> Optional[Dict]:
        """Fallback method for stub server communication."""
        try:
            import requests
            import json
            
            llm_config = settings.get('llm', {})
            endpoint = llm_config.get('endpoint', 'http://localhost:8080/llm')
            timeout = llm_config.get('timeout', 30)
            
            # Prepare request
            request_data = {
                'prompt': prompt,
                'context': {
                    'units': settings.get('processing', {}).get('units_default', 'mm'),
                    'max_operations': settings.get('processing', {}).get('max_operations_per_plan', 50)
                }
            }
            
            # Send request
            response = requests.post(
                endpoint,
                json=request_data,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Stub server request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Stub server request error: {e}")
            return None


class CoPilotInputChangedHandler(adsk.core.InputChangedEventHandler if FUSION_AVAILABLE else object):
    """Handler for input changes in the command dialog."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        """Handle input change events."""
        try:
            if not FUSION_AVAILABLE:
                return
                
            changed_input = args.input
            inputs = args.inputs
            
            # Handle button clicks
            if changed_input.id == 'parse_button' and changed_input.value:
                self.handle_parse_button(inputs)
            elif changed_input.id == 'preview_button' and changed_input.value:
                self.handle_preview_button(inputs)
            elif changed_input.id == 'apply_button' and changed_input.value:
                self.handle_apply_button(inputs)
            
            # Reset button states
            changed_input.value = False
            
        except Exception as e:
            logger.error(f"Error in input changed handler: {e}")
    
    def handle_parse_button(self, inputs):
        """Handle parse button click."""
        results_display = inputs.itemById('results_display')
        results_display.text = "Parse button clicked - functionality would be implemented here"
    
    def handle_preview_button(self, inputs):
        """Handle preview button click."""
        results_display = inputs.itemById('results_display')
        results_display.text = "Preview button clicked - functionality would be implemented here"
    
    def handle_apply_button(self, inputs):
        """Handle apply button click."""
        results_display = inputs.itemById('results_display')
        results_display.text = "Apply button clicked - functionality would be implemented here"


# Development/Testing Functions
def test_components():
    """Test core components in development mode."""
    logger.info("Testing Co-Pilot components...")
    
    # Test settings loading
    test_settings = load_settings()
    logger.info(f"Settings test: {len(test_settings)} sections loaded")
    
    # Test component initialization
    try:
        global settings
        settings = test_settings
        initialize_components()
        logger.info("Component initialization test: PASSED")
    except Exception as e:
        logger.error(f"Component initialization test: FAILED - {e}")
    
    # Test plan processing
    if sanitizer:
        test_plan = {
            "plan_id": "test_001",
            "metadata": {
                "natural_language_prompt": "Create a test cube",
                "units": "mm"
            },
            "operations": [
                {
                    "op_id": "op_1",
                    "op": "create_sketch",
                    "params": {"plane": "XY", "name": "test_sketch"}
                }
            ]
        }
        
        is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(test_plan)
        logger.info(f"Sanitizer test: {'PASSED' if is_valid else 'FAILED'}")
        
        if executor:
            preview_result = executor.preview_plan_in_sandbox(sanitized_plan)
            logger.info(f"Executor preview test: {'PASSED' if preview_result.get('success') else 'FAILED'}")


# Main execution for development/testing
if __name__ == "__main__":
    # Run tests when executed directly (development mode)
    logger.info("Running in development mode")
    test_components()
    logger.info("Development tests completed")
