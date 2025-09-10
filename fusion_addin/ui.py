"""
Fusion 360 Natural-Language CAD Co-Pilot - User Interface

This module provides the user interface components including the chat panel,
preview display, and action log interface.

Author: Fusion CoPilot Team
License: MIT
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Callable
import logging

# Fusion 360 API imports
try:
    import adsk.core
    import adsk.fusion
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

# Configure logging
logger = logging.getLogger(__name__)


class CoPilotUI:
    """
    Main UI controller for the Fusion 360 Co-Pilot.
    
    Manages the chat interface, preview panel, action log, and all user interactions.
    """
    
    def __init__(self, app, ui, settings: Dict):
        """
        Initialize the Co-Pilot UI.
        
        Args:
            app: Fusion 360 application object
            ui: Fusion 360 user interface object
            settings: Configuration settings
        """
        self.app = app
        self.ui = ui
        self.settings = settings
        
        # UI components
        self.palette = None
        self.command_definition = None
        
        # State management
        self.current_plan = None
        self.current_preview = None
        self.action_history = []
        
        # Callbacks for core functionality
        self.parse_callback: Optional[Callable] = None
        self.preview_callback: Optional[Callable] = None
        self.apply_callback: Optional[Callable] = None
        
        # Keep event handlers alive to avoid GC
        self._handlers = []

        logger.info("Co-Pilot UI initialized")
    
    def create_ui(self):
        """Create and show the main Co-Pilot UI."""
        try:
            if FUSION_AVAILABLE:
                self._create_fusion_ui()
            else:
                self._create_mock_ui()
                
            logger.info("Co-Pilot UI created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create UI: {e}")
            raise
    
    def _create_fusion_ui(self):
        """Create the actual Fusion 360 UI components."""
        try:
            print("[CoPilot] _create_fusion_ui: start")
            try:
                self.ui.messageBox("[CoPilot] About to create command definition")
            except Exception:
                pass
            # Create command definition with safe fallback if the icon folder isn't found
            icon_dir = 'resources/commandIcons/'  # Fusion expects RELATIVE path
            abs_icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_dir)
            print(f"[CoPilot] addButtonDefinition using icon dir: {icon_dir} (abs: {abs_icon_dir}) exists={os.path.isdir(abs_icon_dir)}")
            try:
                self.command_definition = self.ui.commandDefinitions.addButtonDefinition(
                    'CoPilotCommand',
                    'CoPilot',
                    'Natural Language CAD Co-Pilot',
                    icon_dir
                )
            except Exception as e:
                try:
                    self.ui.messageBox(f"[CoPilot] Icon dir failed, retry without icons.\n{e}")
                except Exception:
                    pass
                self.command_definition = self.ui.commandDefinitions.addButtonDefinition(
                    'CoPilotCommand',
                    'CoPilot',
                    'Natural Language CAD Co-Pilot'
                )
            try:
                self.ui.messageBox("[CoPilot] Command definition created OK")
            except Exception:
                pass
            print("[CoPilot] addButtonDefinition: ok")
            
            # Create palette for the main interface
            print("[CoPilot] _create_palette: start")
            self._create_palette()
            print("[CoPilot] _create_palette: done")
            
            # Add to toolbar
            print("[CoPilot] _add_to_toolbar: start")
            self._add_to_toolbar()
            print("[CoPilot] _add_to_toolbar: done")
            
        except Exception as e:
            logger.error(f"Failed to create Fusion UI: {e}")
            raise
    
    def _create_palette(self):
        """Create the main Co-Pilot palette."""
        try:
            # Use static HTML file from resources and add a cache-busting query
            base_dir = os.path.dirname(os.path.abspath(__file__))
            html_file_path = os.path.join(base_dir, 'resources', 'palette', 'index.html')
            if not os.path.exists(html_file_path):
                raise FileNotFoundError(f"Palette HTML not found: {html_file_path}")

            # Build a file URL Fusion accepts, with timestamp to avoid caching
            html_url = html_file_path.replace('\\', '/')
            if not html_url.startswith('file://'):
                html_url = f'file://{html_url}'
            from datetime import datetime
            cache_bust = datetime.now().strftime('%Y%m%d%H%M%S')
            html_url = f"{html_url}?v={cache_bust}"

            # Create palette
            print(f"[CoPilot] palettes.add: start, url={html_url}")
            self.palette = self.ui.palettes.add(
                'CoPilotPalette',
                'Co-Pilot',
                html_url,
                True,  # isVisible
                True,  # showCloseButton
                True,  # isResizable
                400,   # width
                600,   # height
                True    # useNewWebBrowser (Chromium webview for adsk.fusionSendData)
            )
            print("[CoPilot] palettes.add: ok")
            
            # Set docking
            dock_position = self.settings.get('ui', {}).get('default_dock_position', 'right')
            if dock_position == 'right':
                self.palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
            elif dock_position == 'left':
                self.palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateLeft
            elif dock_position == 'bottom':
                self.palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateBottom
            else:
                self.palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateFloating
            
            # Add event handlers
            self._setup_palette_handlers()
            # Announce bridge ready to HTML
            try:
                self.update_status("Bridge connected", False)
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"Failed to create palette: {e}")
            raise
    
    def _generate_palette_html(self) -> str:
        """Generate HTML content for the Co-Pilot palette."""
        return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Fusion 360 Co-Pilot</title>
    <style>
        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 10px;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #0696D7, #1E88E5);
            color: white;
            padding: 15px;
            margin: -10px -10px 20px -10px;
            border-radius: 0 0 8px 8px;
        }
        
        .header h1 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
        }
        
        .header p {
            margin: 5px 0 0 0;
            font-size: 12px;
            opacity: 0.9;
        }
        
        .section {
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .section h3 {
            margin: 0 0 10px 0;
            color: #0696D7;
            font-size: 14px;
            font-weight: 600;
        }
        
        .prompt-input {
            width: 100%;
            min-height: 80px;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-family: inherit;
            font-size: 13px;
            resize: vertical;
            box-sizing: border-box;
        }
        
        .prompt-input:focus {
            outline: none;
            border-color: #0696D7;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .btn {
            flex: 1;
            padding: 10px 15px;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background-color: #0696D7;
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #0577B8;
        }
        
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background-color: #545b62;
        }
        
        .btn-success {
            background-color: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background-color: #218838;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .results-area {
            min-height: 120px;
            max-height: 300px;
            overflow-y: auto;
            padding: 10px;
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }
        
        .action-log {
            max-height: 200px;
            overflow-y: auto;
            font-size: 12px;
        }
        
        .log-entry {
            padding: 8px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
        }
        
        .log-entry:last-child {
            border-bottom: none;
        }
        
        .log-status {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 10px;
            flex-shrink: 0;
        }
        
        .log-status.success {
            background-color: #28a745;
        }
        
        .log-status.error {
            background-color: #dc3545;
        }
        
        .log-status.pending {
            background-color: #ffc107;
        }
        
        .log-text {
            flex: 1;
            font-family: inherit;
        }
        
        .log-time {
            font-size: 10px;
            color: #6c757d;
            margin-left: 10px;
        }
        
        .status-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #343a40;
            color: white;
            padding: 8px 15px;
            font-size: 11px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .spinner {
            display: none;
            width: 16px;
            height: 16px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #0696D7;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .example-prompts {
            margin-top: 10px;
        }
        
        .example-prompt {
            background-color: #e9ecef;
            padding: 8px;
            margin: 5px 0;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.2s;
        }
        
        .example-prompt:hover {
            background-color: #dee2e6;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Fusion 360 Co-Pilot</h1>
        <p>Natural Language → CAD Operations</p>
    </div>
    
    <div class="section">
        <h3>💬 Natural Language Input</h3>
        <textarea id="promptInput" class="prompt-input" 
                  placeholder="Describe what you want to create...

Examples:
• Create a 50x30mm plate that's 5mm thick
• Add 4 corner holes, 6mm diameter, 5mm from edges
• Fillet all edges with 2mm radius
• Create a linear pattern of 5 holes spaced 10mm apart"></textarea>
        
        <div class="button-group">
            <button id="parseBtn" class="btn btn-primary">🔍 Parse</button>
            <button id="previewBtn" class="btn btn-secondary" disabled>👁️ Preview</button>
            <button id="applyBtn" class="btn btn-success" disabled>✅ Apply</button>
        </div>
        
        <div class="example-prompts">
            <div class="example-prompt" onclick="setPrompt('Create a 100x50x10mm rectangular plate')">
                📐 Create a 100x50x10mm rectangular plate
            </div>
            <div class="example-prompt" onclick="setPrompt('Add a 6mm hole in the center')">
                🕳️ Add a 6mm hole in the center
            </div>
            <div class="example-prompt" onclick="setPrompt('Fillet all edges with 3mm radius')">
                🔄 Fillet all edges with 3mm radius
            </div>
        </div>
    </div>
    
    <div class="section">
        <h3>📋 Plan Results</h3>
        <div id="resultsArea" class="results-area">Ready for input...</div>
    </div>
    
    <div class="section">
        <h3>📝 Action Log</h3>
        <div id="actionLog" class="action-log">
            <div class="log-entry">
                <div class="log-status success"></div>
                <div class="log-text">Co-Pilot initialized successfully</div>
                <div class="log-time">just now</div>
            </div>
        </div>
    </div>
    
    <div class="status-bar">
        <div>
            <span class="spinner" id="loadingSpinner"></span>
            <span id="statusText">Ready</span>
        </div>
        <div id="connectionStatus">🟢 Local Mode</div>
    </div>
    
    <script>
        // Global state
        let currentPlan = null;
        let isProcessing = false;
        
        // DOM elements
        const promptInput = document.getElementById('promptInput');
        const parseBtn = document.getElementById('parseBtn');
        const previewBtn = document.getElementById('previewBtn');
        const applyBtn = document.getElementById('applyBtn');
        const resultsArea = document.getElementById('resultsArea');
        const actionLog = document.getElementById('actionLog');
        const statusText = document.getElementById('statusText');
        const loadingSpinner = document.getElementById('loadingSpinner');
        
        // Event handlers
        parseBtn.addEventListener('click', handleParse);
        previewBtn.addEventListener('click', handlePreview);
        applyBtn.addEventListener('click', handleApply);
        
        function setPrompt(text) {
            promptInput.value = text;
            promptInput.focus();
        }
        
        function handleParse() {
            const prompt = promptInput.value.trim();
            if (!prompt) {
                showMessage('Please enter a prompt describing what you want to create.', 'error');
                return;
            }
            
            setProcessing(true, 'Parsing natural language...');
            
            // Send message to Fusion add-in
            window.fusionJavaScriptHandler.handle('parse', JSON.stringify({
                action: 'parse',
                prompt: prompt
            }));
        }
        
        function handlePreview() {
            if (!currentPlan) {
                showMessage('No plan available for preview. Parse a prompt first.', 'error');
                return;
            }
            
            setProcessing(true, 'Generating preview...');
            
            window.fusionJavaScriptHandler.handle('preview', JSON.stringify({
                action: 'preview',
                plan: currentPlan
            }));
        }
        
        function handleApply() {
            if (!currentPlan) {
                showMessage('No plan available to apply. Parse a prompt first.', 'error');
                return;
            }
            
            if (!confirm('Apply this plan to your active design? This action cannot be undone.')) {
                return;
            }
            
            setProcessing(true, 'Applying operations...');
            
            window.fusionJavaScriptHandler.handle('apply', JSON.stringify({
                action: 'apply',
                plan: currentPlan
            }));
        }
        
        function setProcessing(processing, message = '') {
            isProcessing = processing;
            parseBtn.disabled = processing;
            previewBtn.disabled = processing || !currentPlan;
            applyBtn.disabled = processing || !currentPlan;
            
            if (processing) {
                loadingSpinner.style.display = 'inline-block';
                statusText.textContent = message;
            } else {
                loadingSpinner.style.display = 'none';
                statusText.textContent = 'Ready';
            }
        }
        
        function showMessage(message, type = 'info') {
            resultsArea.textContent = message;
            addLogEntry(message, type);
        }
        
        function addLogEntry(message, type = 'info') {
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            const status = document.createElement('div');
            status.className = `log-status ${type === 'error' ? 'error' : type === 'success' ? 'success' : 'pending'}`;
            
            const text = document.createElement('div');
            text.className = 'log-text';
            text.textContent = message;
            
            const time = document.createElement('div');
            time.className = 'log-time';
            time.textContent = new Date().toLocaleTimeString();
            
            entry.appendChild(status);
            entry.appendChild(text);
            entry.appendChild(time);
            
            actionLog.insertBefore(entry, actionLog.firstChild);
            
            // Limit log entries
            while (actionLog.children.length > 20) {
                actionLog.removeChild(actionLog.lastChild);
            }
        }
        
        // Handle messages from Fusion add-in
        function handleFusionMessage(message) {
            try {
                const data = JSON.parse(message);
                
                switch (data.type) {
                    case 'parseResult':
                        handleParseResult(data);
                        break;
                    case 'previewResult':
                        handlePreviewResult(data);
                        break;
                    case 'applyResult':
                        handleApplyResult(data);
                        break;
                    case 'error':
                        showMessage(`Error: ${data.message}`, 'error');
                        setProcessing(false);
                        break;
                }
            } catch (e) {
                console.error('Failed to parse message from Fusion:', e);
            }
        }
        
        function handleParseResult(data) {
            setProcessing(false);
            
            if (data.success) {
                currentPlan = data.plan;
                previewBtn.disabled = false;
                applyBtn.disabled = false;
                
                const operations = data.plan.operations || [];
                let resultText = `Plan parsed successfully!\\n\\n`;
                resultText += `Operations (${operations.length}):`;
                
                operations.forEach((op, i) => {
                    resultText += `\\n${i + 1}. ${op.op} (${op.op_id})`;
                });
                
                if (data.warnings && data.warnings.length > 0) {
                    resultText += '\\n\\nWarnings:\\n' + data.warnings.join('\\n');
                }
                
                resultsArea.textContent = resultText;
                addLogEntry(`Plan parsed: ${operations.length} operations`, 'success');
            } else {
                showMessage(`Parse failed: ${data.error}`, 'error');
            }
        }
        
        function handlePreviewResult(data) {
            setProcessing(false);
            
            if (data.success) {
                let resultText = `Preview completed!\\n\\n`;
                resultText += `Features to create: ${data.preview_data.estimated_features.length}\\n`;
                resultText += `Estimated duration: ${data.preview_duration.toFixed(1)}s\\n\\n`;
                resultText += 'Features:\\n';
                
                data.preview_data.estimated_features.forEach((feature, i) => {
                    resultText += `${i + 1}. ${feature}\\n`;
                });
                
                resultsArea.textContent = resultText;
                addLogEntry('Preview generated successfully', 'success');
            } else {
                showMessage(`Preview failed: ${data.error}`, 'error');
            }
        }
        
        function handleApplyResult(data) {
            setProcessing(false);
            
            if (data.success) {
                let resultText = `Operations applied successfully!\\n\\n`;
                resultText += `Execution time: ${data.execution_duration.toFixed(1)}s\\n`;
                resultText += `Features created: ${data.features_created.length}\\n\\n`;
                
                if (data.features_created.length > 0) {
                    resultText += 'Created features:\\n';
                    data.features_created.forEach((feature, i) => {
                        resultText += `${i + 1}. ${feature}\\n`;
                    });
                }
                
                resultsArea.textContent = resultText;
                addLogEntry(`Applied ${data.operations_executed} operations`, 'success');
                
                // Reset for next operation
                currentPlan = null;
                previewBtn.disabled = true;
                applyBtn.disabled = true;
                promptInput.value = '';
            } else {
                showMessage(`Apply failed: ${data.error_message}`, 'error');
            }
        }
        
        // Initialize
        addLogEntry('Co-Pilot UI loaded', 'success');
    </script>
</body>
</html>
        '''
    
    def _setup_palette_handlers(self):
        """Setup event handlers for the palette."""
        try:
            if FUSION_AVAILABLE and self.palette:
                # Add HTML event handler
                html_handler = CoPilotHTMLEventHandler(self)
                self.palette.incomingFromHTML.add(html_handler)
                self._handlers.append(html_handler)
                
                # Add closed event handler
                closed_handler = CoPilotPaletteClosedHandler()
                self.palette.closed.add(closed_handler)
                self._handlers.append(closed_handler)
                
        except Exception as e:
            logger.error(f"Failed to setup palette handlers: {e}")
    
    def _add_to_toolbar(self):
        """Add Co-Pilot button to the toolbar."""
        try:
            if FUSION_AVAILABLE:
                # Get the CREATE panel
                create_panel = self.ui.allToolbarPanels.itemById('SolidCreatePanel')
                if create_panel:
                    # Add command to panel
                    create_panel.controls.addCommand(self.command_definition, '', False)
                    
                    # Connect command handler
                    command_handler = CoPilotCommandCreatedHandler(self)
                    self.command_definition.commandCreated.add(command_handler)
                    
        except Exception as e:
            logger.error(f"Failed to add to toolbar: {e}")
    
    def _create_mock_ui(self):
        """Create mock UI for development mode."""
        logger.info("[MOCK] Co-Pilot UI created in development mode")
        
        # Simulate UI state
        self.palette = {
            'isVisible': True,
            'dockingState': 'right'
        }
    
    def show_palette(self):
        """Show the Co-Pilot palette."""
        try:
            if FUSION_AVAILABLE and self.palette:
                self.palette.isVisible = True
            else:
                logger.info("[MOCK] Showing Co-Pilot palette")
                
        except Exception as e:
            logger.error(f"Failed to show palette: {e}")
    
    def hide_palette(self):
        """Hide the Co-Pilot palette."""
        try:
            if FUSION_AVAILABLE and self.palette:
                self.palette.isVisible = False
            else:
                logger.info("[MOCK] Hiding Co-Pilot palette")
                
        except Exception as e:
            logger.error(f"Failed to hide palette: {e}")
    
    def send_to_html(self, message_type: str, data: Dict):
        """Send a message to the HTML interface."""
        try:
            if FUSION_AVAILABLE and self.palette:
                message = {
                    'type': message_type,
                    **data
                }
                self.palette.sendInfoToHTML('handleFusionMessage', json.dumps(message))
            else:
                logger.info(f"[MOCK] Sending to HTML: {message_type} - {data}")
                
        except Exception as e:
            logger.error(f"Failed to send message to HTML: {e}")
    
    def update_status(self, status: str, is_processing: bool = False):
        """Update the status display."""
        try:
            self.send_to_html('status', {
                'status': status,
                'is_processing': is_processing
            })
            
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
    
    def show_parse_result(self, success: bool, plan: Optional[Dict] = None, 
                         error: Optional[str] = None, warnings: Optional[List[str]] = None):
        """Show the result of plan parsing."""
        try:
            self.send_to_html('parseResult', {
                'success': success,
                'plan': plan,
                'error': error,
                'warnings': warnings or []
            })
            
            if success and plan:
                self.current_plan = plan
                
        except Exception as e:
            logger.error(f"Failed to show parse result: {e}")
    
    def show_preview_result(self, success: bool, preview_data: Optional[Dict] = None,
                           error: Optional[str] = None, duration: float = 0):
        """Show the result of plan preview."""
        try:
            self.send_to_html('previewResult', {
                'success': success,
                'preview_data': preview_data,
                'error': error,
                'preview_duration': duration
            })
            
        except Exception as e:
            logger.error(f"Failed to show preview result: {e}")
    
    def show_apply_result(self, success: bool, execution_result: Optional[Dict] = None,
                         error: Optional[str] = None):
        """Show the result of plan application."""
        try:
            self.send_to_html('applyResult', {
                'success': success,
                'error_message': error,
                **(execution_result or {})
            })
            
            if success:
                self.current_plan = None  # Reset after successful application
                
        except Exception as e:
            logger.error(f"Failed to show apply result: {e}")
    
    def set_callbacks(self, parse_callback: Callable, preview_callback: Callable, 
                     apply_callback: Callable):
        """Set callback functions for UI actions."""
        self.parse_callback = parse_callback
        self.preview_callback = preview_callback
        self.apply_callback = apply_callback
    
    def cleanup(self):
        """Clean up UI components."""
        try:
            if FUSION_AVAILABLE:
                if self.palette:
                    self.palette.deleteMe()
                    self.palette = None
                
                if self.command_definition:
                    self.command_definition.deleteMe()
                    self.command_definition = None
            
            logger.info("Co-Pilot UI cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up UI: {e}")


class CoPilotHTMLEventHandler(adsk.core.HTMLEventHandler if FUSION_AVAILABLE else object):
    """Handler for HTML events from the palette."""
    
    def __init__(self, ui_controller: CoPilotUI):
        super().__init__()
        self.ui_controller = ui_controller
    
    def notify(self, args):
        """Handle HTML events."""
        try:
            if not FUSION_AVAILABLE:
                return
                
            html_args = adsk.core.HTMLEventArgs.cast(args)
            # Prefer action from event args; fallback to JSON payload
            action = getattr(html_args, 'action', None)
            raw = getattr(html_args, 'data', '') or '{}'
            try:
                data = json.loads(raw)
            except Exception:
                data = {}
            if not action:
                action = data.get('action')
            
            logger.debug(f"HTML event received: {action}")
            
            if action == 'parse' and self.ui_controller.parse_callback:
                prompt = data.get('prompt', '')
                self.ui_controller.parse_callback(prompt)
                
            elif action == 'run' and self.ui_controller.parse_callback:
                # Treat run same as parse + immediate preview/apply readiness
                prompt = data.get('prompt', '')
                self.ui_controller.parse_callback(prompt)
                # The Python side will send parseResult; UI can then enable buttons

            elif action == 'preview' and self.ui_controller.preview_callback:
                plan = data.get('plan')
                self.ui_controller.preview_callback(plan)
                
            elif action == 'apply' and self.ui_controller.apply_callback:
                plan = data.get('plan')
                self.ui_controller.apply_callback(plan)
            
            elif action == 'ping':
                # Respond with a status update to prove the bridge works
                self.ui_controller.update_status("Bridge OK", False)
                
        except Exception as e:
            logger.error(f"Error handling HTML event: {e}")


class CoPilotPaletteClosedHandler(adsk.core.UserInterfaceGeneralEventHandler if FUSION_AVAILABLE else object):
    """Handler for palette closed events."""
    
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        """Handle palette closed event."""
        logger.info("Co-Pilot palette closed by user")


class CoPilotCommandCreatedHandler(adsk.core.CommandCreatedEventHandler if FUSION_AVAILABLE else object):
    """Handler for command creation events."""
    
    def __init__(self, ui_controller: CoPilotUI):
        super().__init__()
        self.ui_controller = ui_controller
    
    def notify(self, args):
        """Handle command created event."""
        try:
            if not FUSION_AVAILABLE:
                return
                
            # Show the palette when command is executed
            self.ui_controller.show_palette()
            
        except Exception as e:
            logger.error(f"Error in command created handler: {e}")


# Utility functions for UI management
def create_action_log_html(entries: List[Dict]) -> str:
    """Generate HTML for action log entries."""
    html_entries = []
    
    for entry in entries:
        status_class = 'success' if entry.get('success') else 'error'
        timestamp = entry.get('timestamp', 'unknown')
        message = entry.get('message', 'No message')
        
        html_entries.append(f'''
            <div class="log-entry">
                <div class="log-status {status_class}"></div>
                <div class="log-text">{message}</div>
                <div class="log-time">{timestamp}</div>
            </div>
        ''')
    
    return ''.join(html_entries)


def format_plan_for_display(plan: Dict) -> str:
    """Format a plan for display in the UI."""
    if not plan:
        return "No plan available"
    
    lines = []
    lines.append(f"Plan ID: {plan.get('plan_id', 'unknown')}")
    lines.append(f"Operations: {len(plan.get('operations', []))}")
    
    metadata = plan.get('metadata', {})
    if 'natural_language_prompt' in metadata:
        lines.append(f"Prompt: {metadata['natural_language_prompt']}")
    
    if 'units' in metadata:
        lines.append(f"Units: {metadata['units']}")
    
    operations = plan.get('operations', [])
    if operations:
        lines.append("\nOperations:")
        for i, op in enumerate(operations, 1):
            op_type = op.get('op', 'unknown')
            op_id = op.get('op_id', f'op_{i}')
            lines.append(f"  {i}. {op_type} ({op_id})")
    
    return '\n'.join(lines)


def create_preview_summary(preview_data: Dict) -> str:
    """Create a summary of preview results."""
    if not preview_data:
        return "No preview data available"
    
    lines = []
    
    estimated_features = preview_data.get('estimated_features', [])
    if estimated_features:
        lines.append(f"Features to create: {len(estimated_features)}")
        for i, feature in enumerate(estimated_features, 1):
            lines.append(f"  {i}. {feature}")
    
    bounding_box = preview_data.get('bounding_box_changes', {})
    if bounding_box:
        before = bounding_box.get('before', {})
        after = bounding_box.get('after', {})
        lines.append(f"\nBounding box changes:")
        lines.append(f"  Before: {before}")
        lines.append(f"  After: {after}")
    
    warnings = preview_data.get('warnings', [])
    if warnings:
        lines.append(f"\nWarnings:")
        for warning in warnings:
            lines.append(f"  - {warning}")
    
    return '\n'.join(lines)


# Example usage and testing
if __name__ == "__main__":
    # Test UI components in development mode
    logger.info("Testing Co-Pilot UI components...")
    
    # Mock settings
    test_settings = {
        'ui': {
            'default_dock_position': 'right',
            'theme': 'auto'
        }
    }
    
    # Create UI instance
    ui_controller = CoPilotUI(None, None, test_settings)
    ui_controller.create_ui()
    
    # Test HTML generation
    html_content = ui_controller._generate_palette_html()
    logger.info(f"Generated HTML content: {len(html_content)} characters")
    
    # Test utility functions
    test_plan = {
        'plan_id': 'test_001',
        'metadata': {
            'natural_language_prompt': 'Create a test cube',
            'units': 'mm'
        },
        'operations': [
            {'op_id': 'op_1', 'op': 'create_sketch'},
            {'op_id': 'op_2', 'op': 'extrude'}
        ]
    }
    
    formatted_plan = format_plan_for_display(test_plan)
    logger.info(f"Formatted plan:\n{formatted_plan}")
    
    logger.info("UI testing completed")
