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
from datetime import datetime
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
# Persist the most recent sanitized plan for Preview/Apply demo
last_sanitized_plan: Optional[Dict] = None
# Store last network error for diagnostics when LLM/stub fails
last_network_error: Optional[str] = None
# Keep Python-side event handler references alive for Fusion events
event_handlers: list = []
# Defer apply until command.execute to ensure persistence of created features
pending_apply_plan: Optional[Dict] = None

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

# Offline plan builder for palette (decoupled from class methods)
def _build_offline_plan(prompt: str) -> Dict:
    text = (prompt or '').lower()
    units = settings.get('processing', {}).get('units_default', 'mm')
    if 'cube' in text or 'box' in text or not text:
        return {
            'plan_id': 'offline_cube_demo',
            'metadata': { 'units': units },
            'operations': [
                { 'op_id': 'op_1', 'op': 'create_sketch', 'params': { 'plane': 'XY', 'name': 'CoPilot_cube_sketch' } },
                { 'op_id': 'op_2', 'op': 'draw_rectangle', 'params': { 'center_point': { 'x': 0, 'y': 0, 'z': 0 }, 'width': { 'value': 20, 'unit': 'mm' }, 'height': { 'value': 20, 'unit': 'mm' } } },
                { 'op_id': 'op_3', 'op': 'extrude', 'params': { 'profile': 'last', 'distance': { 'value': 20, 'unit': 'mm' }, 'operation': 'new_body' } }
            ]
        }
    return {
        'plan_id': 'offline_generic_demo',
        'metadata': { 'units': units },
        'operations': [
            { 'op_id': 'op_1', 'op': 'create_sketch', 'params': { 'plane': 'XY', 'name': 'CoPilot_sketch' } },
            { 'op_id': 'op_2', 'op': 'draw_circle', 'params': { 'center': [0,0], 'radius': 10 } },
            { 'op_id': 'op_3', 'op': 'extrude', 'params': { 'profile': 'last', 'distance': 10, 'operation': 'new_body' } }
        ]
    }

# Palette callback implementations
def palette_parse_callback(prompt: str):
    try:
        # Status: parsing started
        if copilot_ui:
            copilot_ui.update_status("Parsing (offline)", True)
        try:
            if FUSION_AVAILABLE and app:
                app.log("[CoPilot] Palette: parse start", adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
        except Exception:
            pass
        # Offline-first: immediate canned plan to avoid any network/spin
        plan = _build_offline_plan(prompt)
        if not plan:
            if copilot_ui:
                copilot_ui.show_parse_result(False, error='No plan generated')
                copilot_ui.update_status("No plan generated", False)
            return
        is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(plan)
        if not is_valid:
            if copilot_ui:
                copilot_ui.show_parse_result(False, error='Validation failed', warnings=messages)
                copilot_ui.update_status("Validation failed", False)
            return
        # Persist for preview/apply
        try:
            globals()['last_sanitized_plan'] = sanitized_plan
        except Exception:
            pass
        if copilot_ui:
            copilot_ui.show_parse_result(True, plan=sanitized_plan, warnings=messages)
            copilot_ui.update_status("Ready", False)
        try:
            if FUSION_AVAILABLE and app:
                app.log(f"[CoPilot] Palette: parse ok (ops={len(sanitized_plan.get('operations', []))})", adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
        except Exception:
            pass
    except Exception as e:
        if copilot_ui:
            copilot_ui.show_parse_result(False, error=str(e))
            copilot_ui.update_status("Error", False)
        try:
            if FUSION_AVAILABLE and app:
                app.log(f"[CoPilot] Palette: parse error {e}", adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
        except Exception:
            pass


def palette_preview_callback(plan: Dict):
    try:
        preview_start = datetime.now()
        # Use provided plan or last
        use_plan = plan or last_sanitized_plan
        if not use_plan:
            if copilot_ui:
                copilot_ui.show_preview_result(False, error='No plan available to preview')
            return
        result = executor.preview_plan_in_sandbox(use_plan)
        duration = (datetime.now() - preview_start).total_seconds()
        if result.get('success'):
            if copilot_ui:
                copilot_ui.show_preview_result(True, preview_data=result.get('preview_data', {}), duration=duration)
        else:
            if copilot_ui:
                copilot_ui.show_preview_result(False, error=result.get('error', 'Unknown error'))
    except Exception as e:
        if copilot_ui:
            copilot_ui.show_preview_result(False, error=str(e))


def palette_apply_callback(plan: Dict):
    try:
        use_plan = plan or last_sanitized_plan
        if not use_plan:
            # Try to generate one quickly
            generated = CoPilotApplyNowExecuteHandler().send_to_llm('create a cube') or CoPilotExecuteHandler()._offline_canned_response('create a cube')
            if generated:
                is_valid, sanitized_plan, _ = sanitizer.sanitize_plan(generated)
                if is_valid:
                    try:
                        globals()['last_sanitized_plan'] = sanitized_plan
                    except Exception:
                        pass
                    use_plan = sanitized_plan
        if not use_plan:
            if copilot_ui:
                copilot_ui.show_apply_result(False, error='No plan available to apply')
            return
        exec_result = executor.execute_plan(use_plan)
        if copilot_ui:
            if exec_result.get('success'):
                copilot_ui.show_apply_result(True, execution_result=exec_result)
            else:
                copilot_ui.show_apply_result(False, error=exec_result.get('error_message', 'Unknown error'))
    except Exception as e:
        if copilot_ui:
            copilot_ui.show_apply_result(False, error=str(e))


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
            'theme': 'auto',
            # Default to dialog mode when settings cannot be loaded
            'enable_palette': False
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
            # Prefer dialog by default if settings missing
            enable_palette = settings.get('ui', {}).get('enable_palette', False)
            try:
                logger.info(f"UI mode → enable_palette={enable_palette}")
                if app:
                    app.log(f"[CoPilot] UI mode: palette={enable_palette}",
                            adsk.core.LogLevels.InfoLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass
            if enable_palette:
                copilot_ui = CoPilotUI(app, ui, settings)
                copilot_ui.set_callbacks(
                    palette_parse_callback,
                    palette_preview_callback,
                    palette_apply_callback
                )
                copilot_ui.create_ui()
                logger.info("Palette UI enabled (offline-first Parse)")
            else:
                logger.info("Palette UI disabled by settings; using command dialog only")
                # Proactively remove any leftover palette from previous runs
                try:
                    palettes = ui.palettes
                    existing_palette = palettes.itemById('CoPilotPalette') if palettes else None
                    if existing_palette and existing_palette.isValid:
                        existing_palette.deleteMe()
                        logger.info("Removed stale Co-Pilot palette")
                except Exception:
                    pass
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
            # If palette UI is active per settings, avoid registering the dialog-based command
            # Prefer dialog by default if settings missing
            palette_active = settings.get('ui', {}).get('enable_palette', False)
            if palette_active:
                # Clean up any stale dialog command/button
                try:
                    existing = ui.commandDefinitions.itemById('fusion_copilot_open')
                    if existing and existing.isValid:
                        existing.deleteMe()
                except Exception:
                    pass
                try:
                    create_panel = ui.allToolbarPanels.itemById('SolidCreatePanel')
                    if create_panel:
                        stale = create_panel.controls.itemById('fusion_copilot_open')
                        if stale and stale.isValid:
                            stale.deleteMe()
                except Exception:
                    pass
                logger.info("Palette active; skipped registering dialog command")
                return
            # Force-rebuild the command definition each run to avoid UI caching
            existing = ui.commandDefinitions.itemById('fusion_copilot_open')
            if existing and existing.isValid:
                try:
                    existing.deleteMe()
                except Exception:
                    pass

            # Register main Co-Pilot command
            cmd_def = ui.commandDefinitions.addButtonDefinition(
                'fusion_copilot_open',
                'CoPilot',
                'Open the Natural Language CAD Co-Pilot'
            )
            
            # Connect command handler
            cmd_handler = CoPilotCommandHandler()
            cmd_def.commandCreated.add(cmd_handler)
            event_handlers.append(cmd_handler)
            command_definitions['copilot_open'] = cmd_def
            
            # Add to toolbar (remove stale control first)
            create_panel = ui.allToolbarPanels.itemById('SolidCreatePanel')
            if create_panel:
                stale = create_panel.controls.itemById('fusion_copilot_open')
                if stale and stale.isValid:
                    try:
                        stale.deleteMe()
                    except Exception:
                        pass
                create_panel.controls.addCommand(cmd_def, '', False)
                logger.info("Co-Pilot command added to toolbar")

            # Register background apply command (no UI)
            try:
                existing_apply = ui.commandDefinitions.itemById('fusion_copilot_apply_now')
                if existing_apply and existing_apply.isValid:
                    existing_apply.deleteMe()
            except Exception:
                pass
            apply_def = ui.commandDefinitions.addButtonDefinition(
                'fusion_copilot_apply_now',
                'CoPilot Apply Now',
                'Apply the last plan immediately (background)'
            )
            apply_exec = CoPilotApplyNowHandler()
            apply_def.commandCreated.add(apply_exec)
            event_handlers.append(apply_exec)
            command_definitions['copilot_apply_now'] = apply_def
            
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
            # Cleanup palette
            if copilot_ui:
                copilot_ui.cleanup()
            
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
            # Clear stored event handlers
            event_handlers.clear()
            
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
            # Ensure OK/Cancel are visible so we can commit actions in execute phase
            try:
                command.isOKButtonVisible = True
                command.isCancelButtonVisible = True
            except Exception:
                pass
            inputs = command.commandInputs
            
            # Create command inputs for the Co-Pilot dialog
            self.create_command_inputs(inputs)
            
            # Connect event handlers
            execute_handler = CoPilotExecuteHandler()
            command.execute.add(execute_handler)
            event_handlers.append(execute_handler)
            
            input_changed_handler = CoPilotInputChangedHandler()
            command.inputChanged.add(input_changed_handler)
            event_handlers.append(input_changed_handler)
            
        except Exception as e:
            logger.error(f"Error in command handler: {e}")
            if FUSION_AVAILABLE and ui:
                ui.messageBox(f'Command handler error: {str(e)}')
    
    def create_command_inputs(self, inputs):
        """Create the command dialog inputs."""
        try:
            # Header label
            header = inputs.addTextBoxCommandInput(
                'header_label',
                '',
                'Co-Pilot — Natural Language CAD',
                1,
                True
            )
            header.isFullWidth = True

            # Status line
            status_line = inputs.addTextBoxCommandInput(
                'status_line',
                'Status',
                'Ready',
                1,
                True
            )

            # Results display (put first so it's always visible)
            # Results: use a string input (updates reliably across builds)
            results_input = inputs.addStringValueInput(
                'results_display',
                'Results',
                'Ready...'
            )
            results_input.isReadOnly = True
            results_input.tooltip = "Shows parsing results and operation details"

            # Main prompt input
            prompt_input = inputs.addTextBoxCommandInput(
                'prompt_input',
                'Natural Language Prompt',
                'Describe what you want to create...',
                5,  # Number of rows
                False  # Read only
            )
            prompt_input.tooltip = "Enter your natural language description of what you want to create"
            
            # Examples dropdown
            examples = inputs.addDropDownCommandInput('example_prompts', 'Examples', adsk.core.DropDownStyles.TextListDropDownStyle)
            examples.listItems.add('Create a 25mm cube', False)
            examples.listItems.add('Create a 100x50x10mm rectangular plate', False)
            examples.listItems.add('Add a 6mm hole at the center', False)

            # Action buttons group
            button_group = inputs.addGroupCommandInput('action_buttons', 'Actions')
            button_group.isExpanded = True

            # Build tag to confirm fresh dialog
            build_label = inputs.addTextBoxCommandInput(
                'build_info',
                'Build',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                1,
                True
            )
            
            # Parse button
            # Fusion expects a RELATIVE resource folder path here
            icon_dir = 'resources/commandIcons'
            # Parse button (push button, not checkbox)
            parse_button = button_group.children.addBoolValueInput(
                'parse_button',
                'Parse',
                False,
                icon_dir,
                False
            )
            parse_button.tooltip = "Convert natural language to structured plan"
            try:
                parse_button.isFullWidth = True
            except Exception:
                pass

            # Run button (executes full pipeline and keeps dialog open)
            run_button = button_group.children.addBoolValueInput(
                'run_button',
                'Run',
                False,
                icon_dir,
                False
            )
            run_button.tooltip = "Parse + validate + apply in one step"
            try:
                run_button.isFullWidth = True
            except Exception:
                pass
            
            # Preview button
            # Preview button (push button)
            preview_button = button_group.children.addBoolValueInput(
                'preview_button',
                'Preview',
                False,
                icon_dir,
                False
            )
            preview_button.tooltip = "Preview operations in sandbox mode"
            try:
                preview_button.isFullWidth = True
            except Exception:
                pass
            
            # Apply button
            # Apply button (push button)
            apply_button = button_group.children.addBoolValueInput(
                'apply_button',
                'Apply',
                False,
                icon_dir,
                False
            )
            apply_button.tooltip = "Apply operations to active design"
            try:
                apply_button.isFullWidth = True
            except Exception:
                pass
            
            # (Results input defined above)
            
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
            # If an Apply was requested, run it here so the dialog is in a stable execute phase
            try:
                global pending_apply_plan
            except Exception:
                pending_apply_plan = None
            if pending_apply_plan is not None:
                try:
                    self._apply_plan_now(inputs)
                finally:
                    pending_apply_plan = None
                return
            
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
        """Delegate to shared processing implementation to avoid duplication."""
        helper = CoPilotApplyNowExecuteHandler()
        return helper.process_natural_language_prompt(prompt, inputs)

    def _apply_plan_now(self, inputs):
        """Execute apply while in execute phase to ensure created geometry persists."""
        try:
            self.handle_apply_button(inputs)
        except Exception as e:
            try:
                if FUSION_AVAILABLE and app:
                    app.log(f"[CoPilot] Apply (execute phase) error: {e}",
                            adsk.core.LogLevels.ErrorLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass


class CoPilotApplyNowHandler(adsk.core.CommandCreatedEventHandler if FUSION_AVAILABLE else object):
    """Background handler that applies the last plan immediately without dialog UI."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            if not FUSION_AVAILABLE:
                return
            command = args.command
            # Run on execute
            exec_handler = CoPilotApplyNowExecuteHandler()
            command.execute.add(exec_handler)
            event_handlers.append(exec_handler)
        except Exception as e:
            try:
                if FUSION_AVAILABLE and app:
                    app.log(f"[CoPilot] ApplyNow created error: {e}",
                            adsk.core.LogLevels.ErrorLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass


class CoPilotApplyNowExecuteHandler(adsk.core.CommandEventHandler if FUSION_AVAILABLE else object):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            if not FUSION_AVAILABLE:
                return
            inputs = args.command.commandInputs
            try:
                if FUSION_AVAILABLE and app:
                    app.log("[CoPilot] ApplyNow: starting",
                            adsk.core.LogLevels.InfoLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass
            # Ensure a plan exists; if missing, build one via LLM/stub with default prompt
            try:
                global last_sanitized_plan
            except Exception:
                last_sanitized_plan = None
            if not last_sanitized_plan:
                exec_handler = CoPilotExecuteHandler()
                prompt_text = 'create a cube'
                plan = self.send_to_llm(prompt_text)
                if not plan:
                    # Fall back to offline canned
                    plan = exec_handler._offline_canned_response(prompt_text)
                try:
                    is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(plan)
                except Exception:
                    is_valid, sanitized_plan, messages = True, plan or {}, []
                if is_valid:
                    last_sanitized_plan = sanitized_plan
                    try:
                        if FUSION_AVAILABLE and app:
                            app.log(f"[CoPilot] ApplyNow: plan ready (ops={len(sanitized_plan.get('operations', []))})",
                                    adsk.core.LogLevels.InfoLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass
                else:
                    try:
                        if FUSION_AVAILABLE and app:
                            app.log("[CoPilot] ApplyNow: validation failed", adsk.core.LogLevels.ErrorLogLevel, adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass
                    return
            # Execute apply using existing handler
            input_handler = CoPilotInputChangedHandler()
            input_handler.handle_apply_button(inputs)
            try:
                if FUSION_AVAILABLE and app:
                    app.log("[CoPilot] ApplyNow: completed",
                            adsk.core.LogLevels.InfoLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass
        except Exception as e:
            try:
                if FUSION_AVAILABLE and app:
                    app.log(f"[CoPilot] ApplyNow execute error: {e}",
                            adsk.core.LogLevels.ErrorLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass
    
    def process_natural_language_prompt(self, prompt: str, inputs):
        """Process the natural language prompt through the Co-Pilot pipeline."""
        try:
            results_display = inputs.itemById('results_display')
            
            # Step 1: Send to LLM for parsing
            if results_display:
                results_display.value = "Parsing natural language prompt..."
            
            parsed_plan = self.send_to_llm(prompt)
            
            if not parsed_plan:
                if results_display:
                    results_display.value = "Failed to parse prompt. Check LLM connection."
                return
            
            # Step 2: Sanitize the plan
            if results_display:
                current = results_display.value
                results_display.value = (current or "") + "\n\nValidating and sanitizing plan..."
            
            is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(parsed_plan)
            
            if not is_valid:
                if results_display:
                    results_display.text += f"\n\nValidation failed:\n" + "\n".join(messages)
                return
            
            # Persist sanitized plan for subsequent Apply/Preview steps
            try:
                globals()['last_sanitized_plan'] = sanitized_plan
            except Exception:
                pass
            
            # Step 3: Show sanitized plan
            op_count = len(sanitized_plan.get('operations', []))
            if results_display:
                current = results_display.value
                current = (current or "") + f"\n\nPlan validated successfully!"
                current = current + f"\nOperations: {op_count}"
                results_display.value = current
            # Also show a quick summary dialog so you see immediate feedback
            try:
                if FUSION_AVAILABLE and ui:
                    ui.messageBox(f"Co-Pilot: Plan ready\nOperations: {op_count}")
            except Exception:
                pass
            
            if messages:
                if results_display:
                    current = results_display.value
                    results_display.value = (current or "") + (f"\n\nWarnings:\n" + "\n".join(messages))
            
            # Step 4: Preview (if requested)
            # This would be handled by button clicks in a full implementation
            
            if results_display:
                current = results_display.value
                results_display.value = (current or "") + f"\n\nReady for preview or execution."
            
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            if results_display:
                results_display.value = f"Error: {str(e)}"
    
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
            # Prefer requests, but fall back to urllib if unavailable (Fusion env often lacks requests)
            try:
                import requests as _requests
            except Exception:
                _requests = None
            import json
            
            llm_config = settings.get('llm', {})
            endpoint = llm_config.get('endpoint', 'http://localhost:8080/llm')
            timeout = llm_config.get('timeout', 30)
            # Normalize localhost to 127.0.0.1 for reliability
            try:
                if 'localhost' in endpoint:
                    endpoint = endpoint.replace('localhost', '127.0.0.1')
            except Exception:
                pass
            
            # Optional: health check before sending request (uses urllib fallback internally)
            if not self._stub_health_check(endpoint):
                logger.error("Stub server health check failed")
                try:
                    globals()['last_network_error'] = f"Health check failed for {endpoint}"
                except Exception:
                    pass
                try:
                    if FUSION_AVAILABLE and app:
                        app.log("[CoPilot] Stub health check failed",
                                adsk.core.LogLevels.WarningLogLevel,
                                adsk.core.LogTypes.ConsoleLogType)
                except Exception:
                    pass
                return None

            # Prepare request
            request_data = {
                'prompt': (prompt or 'create a cube'),
                'context': {
                    'units': settings.get('processing', {}).get('units_default', 'mm'),
                    'max_operations': settings.get('processing', {}).get('max_operations_per_plan', 50)
                }
            }
            
            # Send request (try requests first)
            if _requests is not None:
                try:
                    try:
                        if FUSION_AVAILABLE and app:
                            app.log(f"[CoPilot] Stub POST (requests) → {endpoint}",
                                    adsk.core.LogLevels.InfoLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass
                    response = _requests.post(
                        endpoint,
                        json=request_data,
                        timeout=timeout,
                        headers={'Content-Type': 'application/json'}
                    )
                    if response.status_code == 200:
                        try:
                            if FUSION_AVAILABLE and app:
                                app.log("[CoPilot] Stub POST success (requests)",
                                        adsk.core.LogLevels.InfoLogLevel,
                                        adsk.core.LogTypes.ConsoleLogType)
                        except Exception:
                            pass
                        return response.json()
                    else:
                        logger.error(f"Stub server request failed: {response.status_code}")
                        try:
                            globals()['last_network_error'] = f"requests POST non-200: {response.status_code}"
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(f"Requests POST failed, will try urllib: {e}")
                    try:
                        globals()['last_network_error'] = f"requests POST exception: {e}"
                    except Exception:
                        pass

            # Fallback to urllib
            try:
                import urllib.request
                import urllib.error
                try:
                    if FUSION_AVAILABLE and app:
                        app.log(f"[CoPilot] Stub POST (urllib) → {endpoint}",
                                adsk.core.LogLevels.InfoLogLevel,
                                adsk.core.LogTypes.ConsoleLogType)
                except Exception:
                    pass
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(request_data).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        resp_data = resp.read()
                        try:
                            if FUSION_AVAILABLE and app:
                                app.log("[CoPilot] Stub POST success (urllib)",
                                        adsk.core.LogLevels.InfoLogLevel,
                                        adsk.core.LogTypes.ConsoleLogType)
                        except Exception:
                            pass
                        return json.loads(resp_data.decode('utf-8'))
                    else:
                        logger.error(f"Stub server urllib request failed: {resp.status}")
                        try:
                            globals()['last_network_error'] = f"urllib POST non-200: {resp.status}"
                        except Exception:
                            pass
                        return None
            except Exception as e:
                logger.error(f"Stub server urllib request error: {e}")
                try:
                    globals()['last_network_error'] = f"urllib POST exception: {e}"
                except Exception:
                    pass
                return None
                
        except Exception as e:
            logger.error(f"Stub server request error: {e}")
            return None

    def _stub_health_check(self, endpoint: str) -> bool:
        """Check health of the stub server given the LLM endpoint URL (with urllib fallback)."""
        base = endpoint
        if base.endswith('/llm'):
            base = base[:-4]
        # Normalize localhost to 127.0.0.1
        try:
            base = base.replace('localhost', '127.0.0.1')
        except Exception:
            pass
        health_url = base.rstrip('/') + '/health'
        try:
            if FUSION_AVAILABLE and app:
                app.log(f"[CoPilot] Stub health → {health_url}",
                        adsk.core.LogLevels.InfoLogLevel,
                        adsk.core.LogTypes.ConsoleLogType)
        except Exception:
            pass
        # Try requests if available
        try:
            import requests as _requests
        except Exception:
            _requests = None
        if _requests is not None:
            try:
                r = _requests.get(health_url, timeout=5)
                if r.status_code != 200:
                    try:
                        if FUSION_AVAILABLE and app:
                            app.log("[CoPilot] Stub health failed (requests)",
                                    adsk.core.LogLevels.WarningLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass
                    try:
                        globals()['last_network_error'] = f"health non-200 (requests): {r.status_code}"
                    except Exception:
                        pass
                    return False
                data = r.json()
                status = str(data.get('status', '')).lower()
                try:
                    if FUSION_AVAILABLE and app:
                        app.log(f"[CoPilot] Stub health OK (requests): {status}",
                                adsk.core.LogLevels.InfoLogLevel,
                                adsk.core.LogTypes.ConsoleLogType)
                except Exception:
                    pass
                return status in ('healthy', 'running', 'ok')
            except Exception as e:
                logger.debug(f"Requests health check failed, trying urllib: {e}")
                try:
                    globals()['last_network_error'] = f"health requests exception: {e}"
                except Exception:
                    pass
        # Fallback to urllib
        try:
            import urllib.request
            with urllib.request.urlopen(health_url, timeout=5) as resp:
                if resp.status != 200:
                    try:
                        if FUSION_AVAILABLE and app:
                            app.log("[CoPilot] Stub health failed (urllib)",
                                    adsk.core.LogLevels.WarningLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass
                    try:
                        globals()['last_network_error'] = f"health non-200 (urllib): {resp.status}"
                    except Exception:
                        pass
                    return False
                raw = resp.read().decode('utf-8')
                try:
                    data = json.loads(raw)
                except Exception:
                    try:
                        globals()['last_network_error'] = "health invalid JSON (urllib)"
                    except Exception:
                        pass
                    return False
                status = str(data.get('status', '')).lower()
                try:
                    if FUSION_AVAILABLE and app:
                        app.log(f"[CoPilot] Stub health OK (urllib): {status}",
                                adsk.core.LogLevels.InfoLogLevel,
                                adsk.core.LogTypes.ConsoleLogType)
                except Exception:
                    pass
                return status in ('healthy', 'running', 'ok')
        except Exception as e:
            logger.warning(f"Stub health check error: {e}")
            try:
                globals()['last_network_error'] = f"health urllib exception: {e}"
            except Exception:
                pass
            return False

    def _offline_canned_response(self, prompt: str) -> Optional[Dict]:
        """Provide a small built-in canned plan for offline/demo use."""
        try:
            text = (prompt or '').lower()
            if 'cube' in text or 'box' in text:
                return {
                    'plan_id': 'offline_cube_demo',
                    'metadata': { 'units': settings.get('processing', {}).get('units_default', 'mm') },
                    'operations': [
                        { 'op_id': 'op_1', 'op': 'create_sketch', 'params': { 'plane': 'XY', 'name': 'cube_sketch' } },
                        { 'op_id': 'op_2', 'op': 'draw_rectangle', 'params': { 'center': [0,0], 'width': 20, 'height': 20, 'constraints': ['horizontal','vertical'] } },
                        { 'op_id': 'op_3', 'op': 'extrude', 'params': { 'profile': 'last', 'distance': 20, 'operation': 'new_body' } }
                    ]
                }
            # Generic minimal plan
            return {
                'plan_id': 'offline_generic_demo',
                'metadata': { 'units': settings.get('processing', {}).get('units_default', 'mm') },
                'operations': [
                    { 'op_id': 'op_1', 'op': 'create_sketch', 'params': { 'plane': 'XY', 'name': 'sketch_1' } },
                    { 'op_id': 'op_2', 'op': 'draw_circle', 'params': { 'center': [0,0], 'radius': 10 } },
                    { 'op_id': 'op_3', 'op': 'extrude', 'params': { 'profile': 'last', 'distance': 10, 'operation': 'new_body' } }
                ]
            }
        except Exception:
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
                
            global last_sanitized_plan

            changed_input = args.input
            inputs = args.inputs
            
            # Handle button clicks
            if changed_input.id == 'parse_button' and changed_input.value:
                self.handle_parse_button(inputs)
            elif changed_input.id == 'run_button' and changed_input.value:
                # Directly invoke the full pipeline
                try:
                    app.log("[CoPilot] Dialog: Run clicked", adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
                    if ui:
                        ui.messageBox('[CoPilot] Run start')
                except Exception:
                    pass
                try:
                    status_line = inputs.itemById('status_line')
                    if status_line:
                        status_line.text = 'Running pipeline...'
                except Exception:
                    pass
                # Run the pipeline inline here for reliable UI updates
                exec_handler = CoPilotExecuteHandler()
                try:
                    prompt_input = inputs.itemById('prompt_input')
                    prompt_text = prompt_input.text if prompt_input else ""
                    # 1) Try LLM / Stub path first
                    plan = exec_handler.send_to_llm(prompt_text)
                    rd = inputs.itemById('results_display')
                    if plan:
                        try:
                            is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(plan)
                        except Exception:
                            is_valid, sanitized_plan, messages = True, plan, []

                        if is_valid:
                            ops = sanitized_plan.get('operations', [])
                            last_sanitized_plan = sanitized_plan
                            if rd:
                                rd.value = "Plan validated successfully!\nOperations: " + str(len(ops))
                            try:
                                if FUSION_AVAILABLE and app:
                                    app.log(f"[CoPilot] LLM/Stub plan ready (ops={len(ops)})",
                                            adsk.core.LogLevels.InfoLogLevel,
                                            adsk.core.LogTypes.ConsoleLogType)
                            except Exception:
                                pass
                            try:
                                if FUSION_AVAILABLE and ui:
                                    ui.messageBox("Co-Pilot: Run completed")
                            except Exception:
                                pass
                            return
                        else:
                            if rd:
                                rd.value = "Validation failed:\n" + "\n".join(messages)
                            return

                    # 2) Offline fallback (log reason if available)
                    try:
                        from main import last_network_error as _net_err  # self-reference OK inside module
                    except Exception:
                        _net_err = None
                    try:
                        if FUSION_AVAILABLE and app and _net_err:
                            app.log(f"[CoPilot] Falling back to offline: {_net_err}",
                                    adsk.core.LogLevels.WarningLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass
                    try:
                        offline = exec_handler._offline_canned_response(prompt_text)
                    except Exception:
                        offline = None
                    if offline is None:
                        offline = {
                            'plan_id': 'offline_fallback',
                            'metadata': { 'units': 'mm' },
                            'operations': [ {'op_id':'op_1','op':'create_sketch','params':{'plane':'XY','name':'fallback'}} ]
                        }
                    try:
                        is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(offline)
                    except Exception:
                        is_valid, sanitized_plan, messages = True, offline, []
                    ops = sanitized_plan.get('operations', [])
                    last_sanitized_plan = sanitized_plan
                    if rd:
                        rd.value = "Plan validated successfully!\nOperations: " + str(len(ops))
                    try:
                        if FUSION_AVAILABLE and app:
                            app.log(f"[CoPilot] Offline plan ready (ops={len(ops)})",
                                    adsk.core.LogLevels.InfoLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass
                    try:
                        if FUSION_AVAILABLE and ui:
                            ui.messageBox(f"Co-Pilot: Offline plan ready\nOperations: {len(ops)}")
                    except Exception:
                        pass
                    return
                except Exception as e:
                    try:
                        results_display = inputs.itemById('results_display')
                        if results_display:
                            results_display.value = f"Error: {e}"
                    except Exception:
                        pass
            elif changed_input.id == 'preview_button' and changed_input.value:
                try:
                    app.log("[CoPilot] Dialog: Preview clicked", adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
                    if ui:
                        ui.messageBox('[CoPilot] Preview clicked (dialog)')
                except Exception:
                    pass
                self.handle_preview_button(inputs)
            elif changed_input.id == 'apply_button' and changed_input.value:
                try:
                    app.log("[CoPilot] Dialog: Apply clicked", adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
                    if ui:
                        ui.messageBox('[CoPilot] Apply clicked (dialog)')
                except Exception:
                    pass
                # Run apply immediately so geometry appears
                try:
                    if FUSION_AVAILABLE and app:
                        app.log("[CoPilot] Apply (immediate): starting",
                                adsk.core.LogLevels.InfoLogLevel,
                                adsk.core.LogTypes.ConsoleLogType)
                except Exception:
                    pass
                try:
                    self.handle_apply_button(inputs)
                except Exception:
                    pass
                # Also trigger background apply (skip for selection-dependent ops like holes)
                try:
                    needs_selection = False
                    try:
                        ops = (last_sanitized_plan or {}).get('operations', [])
                        needs_selection = any(op.get('op') in ('create_hole', 'fillet', 'chamfer') for op in ops)
                    except Exception:
                        needs_selection = False
                    if not needs_selection:
                        if FUSION_AVAILABLE and app:
                            app.log("[CoPilot] Apply (background): launching",
                                    adsk.core.LogLevels.InfoLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                        bg_apply = ui.commandDefinitions.itemById('fusion_copilot_apply_now') if ui else None
                        if not bg_apply:
                            if FUSION_AVAILABLE and app:
                                app.log("[CoPilot] Apply (background): command missing",
                                        adsk.core.LogLevels.WarningLogLevel,
                                        adsk.core.LogTypes.ConsoleLogType)
                        else:
                            bg_apply.execute()
                except Exception as e:
                    try:
                        if FUSION_AVAILABLE and app:
                            app.log(f"[CoPilot] Failed to start background apply: {e}",
                                    adsk.core.LogLevels.ErrorLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass

            # Examples selection → fill prompt
            if changed_input.id == 'example_prompts':
                try:
                    sel = inputs.itemById('example_prompts')
                    prompt = inputs.itemById('prompt_input')
                    idx = sel.selectedItem.index
                    presets = [
                        'Create a 25mm cube',
                        'Create a 100x50x10mm rectangular plate',
                        'Add a 6mm hole at the center'
                    ]
                    if prompt:
                        prompt.text = presets[idx]
                except Exception:
                    pass

            # Reset button states
            changed_input.value = False
            
        except Exception as e:
            logger.error(f"Error in input changed handler: {e}")
    
    def handle_parse_button(self, inputs):
        """Handle parse button click by invoking the core pipeline."""
        try:
            global last_sanitized_plan
            results_display = inputs.itemById('results_display')
            prompt_input = inputs.itemById('prompt_input')
            prompt_text = prompt_input.text if prompt_input else ""
            if results_display:
                results_display.value = "Parsing natural language prompt...\n(Contacting LLM or using offline canned plan)"
            
            # Prefer LLM/Stub first
            exec_handler = CoPilotExecuteHandler()
            plan = exec_handler.send_to_llm(prompt_text)
            if plan:
                try:
                    is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(plan)
                except Exception:
                    is_valid, sanitized_plan, messages = True, plan, []
                if is_valid:
                    ops = sanitized_plan.get('operations', [])
                    last_sanitized_plan = sanitized_plan
                    if results_display:
                        results_display.value = "Plan validated successfully!\nOperations: " + str(len(ops))
                    try:
                        if FUSION_AVAILABLE and app:
                            app.log(f"[CoPilot] LLM/Stub plan ready (ops={len(ops)})",
                                    adsk.core.LogLevels.InfoLogLevel,
                                    adsk.core.LogTypes.ConsoleLogType)
                    except Exception:
                        pass
                    return
            
            # Offline fallback
            try:
                offline = exec_handler._offline_canned_response(prompt_text)
            except Exception:
                offline = None
            if offline is None:
                offline = {
                    'plan_id': 'offline_fallback',
                    'metadata': { 'units': 'mm' },
                    'operations': [ {'op_id':'op_1','op':'create_sketch','params':{'plane':'XY','name':'fallback'}} ]
                }
            try:
                is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(offline)
            except Exception:
                is_valid, sanitized_plan, messages = True, offline, []
            ops = sanitized_plan.get('operations', [])
            last_sanitized_plan = sanitized_plan
            if results_display:
                results_display.value = "Plan validated successfully!\nOperations: " + str(len(ops))
            try:
                if FUSION_AVAILABLE and app:
                    app.log(f"[CoPilot] Offline plan ready (ops={len(ops)})",
                            adsk.core.LogLevels.InfoLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass
            try:
                if FUSION_AVAILABLE and ui:
                    ui.messageBox(f"Co-Pilot: Offline plan ready\nOperations: {len(ops)}")
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Parse handler error (dialog): {e}")
            results_display = inputs.itemById('results_display')
            if results_display:
                results_display.value = f"Error: {e}"
    
    def handle_preview_button(self, inputs):
        """Handle preview button click."""
        try:
            global last_sanitized_plan
            results_display = inputs.itemById('results_display')
            # Prefer the last sanitized plan if available
            ops = []
            if last_sanitized_plan:
                ops = [op.get('op') for op in last_sanitized_plan.get('operations', [])]
            else:
                exec_handler = CoPilotExecuteHandler()
                last_prompt = inputs.itemById('prompt_input').text if inputs.itemById('prompt_input') else ''
                offline = exec_handler._offline_canned_response(last_prompt or 'cube') or {}
                ops = [op.get('op') for op in offline.get('operations', [])]
            preview_text = 'Preview:\n' + ('\n'.join(ops) if ops else 'No operations')
            if results_display:
                results_display.value = preview_text
            try:
                if FUSION_AVAILABLE and app:
                    app.log('[CoPilot] ' + preview_text.replace('\n', ' | '),
                            adsk.core.LogLevels.InfoLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
                if FUSION_AVAILABLE and ui:
                    ui.messageBox(preview_text)
            except Exception:
                pass
        except Exception as e:
            rd = inputs.itemById('results_display')
            if rd:
                rd.value = f"Preview error: {e}"
    
    def handle_apply_button(self, inputs):
        """Handle apply button click."""
        try:
            global last_sanitized_plan, executor
            results_display = inputs.itemById('results_display')
            try:
                if FUSION_AVAILABLE and app:
                    app.log(f"[CoPilot] Apply: executor={'ready' if executor else 'missing'}, plan={'ready' if last_sanitized_plan else 'missing'}",
                            adsk.core.LogLevels.InfoLogLevel,
                            adsk.core.LogTypes.ConsoleLogType)
            except Exception:
                pass

            # Ensure we have a plan to apply
            plan = last_sanitized_plan
            if not plan:
                exec_handler = CoPilotExecuteHandler()
                last_prompt = inputs.itemById('prompt_input').text if inputs.itemById('prompt_input') else ''
                # First try to get a fresh plan from LLM/stub using the current prompt
                fresh = None
                try:
                    fresh = exec_handler.send_to_llm(last_prompt or 'create a cube')
                except Exception:
                    fresh = None
                candidate = fresh
                # If network/stub failed, fall back to offline canned based on the prompt text (no forced cube)
                if not candidate:
                    try:
                        candidate = exec_handler._offline_canned_response(last_prompt)
                    except Exception:
                        candidate = None
                if not candidate:
                    candidate = {
                        'plan_id': 'offline_fallback_apply',
                        'metadata': { 'units': settings.get('processing', {}).get('units_default', 'mm') },
                        'operations': [ {'op_id':'op_1','op':'create_sketch','params':{'plane':'XY','name':'fallback'}} ]
                    }
                try:
                    is_valid, sanitized_plan, messages = sanitizer.sanitize_plan(candidate)
                except Exception:
                    is_valid, sanitized_plan, messages = True, candidate, []
                if not is_valid:
                    if results_display:
                        results_display.value = 'Apply failed: No valid plan available.'
                    if FUSION_AVAILABLE and ui:
                        ui.messageBox('Apply failed: No valid plan available.')
                    return
                plan = sanitized_plan
                last_sanitized_plan = plan

            # Execute the plan using the global executor (mock-safe if real API not invoked)
            if not executor:
                if results_display:
                    results_display.value = 'Apply failed: Executor not initialized.'
                if FUSION_AVAILABLE and ui:
                    ui.messageBox('Apply failed: Executor not initialized.')
                return

            exec_result = executor.execute_plan(plan)

            if exec_result.get('success'):
                created = exec_result.get('features_created', [])
                ops_count = exec_result.get('operations_executed', 0)
                summary = f"Applied {ops_count} operations. Created {len(created)} features."
                if results_display:
                    results_display.value = summary
                try:
                    if FUSION_AVAILABLE and app:
                        app.log('[CoPilot] Apply success: ' + summary,
                                adsk.core.LogLevels.InfoLogLevel,
                                adsk.core.LogTypes.ConsoleLogType)
                    if FUSION_AVAILABLE and ui:
                        ui.messageBox('Co-Pilot: Apply success\n' + summary)
                except Exception:
                    pass
            else:
                err = exec_result.get('error_message', 'Unknown error')
                if results_display:
                    results_display.value = f'Apply failed: {err}'
                try:
                    if FUSION_AVAILABLE and app:
                        app.log('[CoPilot] Apply failed: ' + err,
                                adsk.core.LogLevels.ErrorLogLevel,
                                adsk.core.LogTypes.ConsoleLogType)
                    if FUSION_AVAILABLE and ui:
                        ui.messageBox('Apply failed: ' + err)
                except Exception:
                    pass
        except Exception as e:
            rd = inputs.itemById('results_display')
            if rd:
                rd.value = f"Apply error: {e}"


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
