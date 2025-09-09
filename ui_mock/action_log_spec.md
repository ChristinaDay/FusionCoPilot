# Fusion 360 Co-Pilot - Action Log UI Specification

## Overview

This document specifies the user interface design and behavior for the Fusion 360 Co-Pilot action log and preview system. The UI provides real-time feedback, operation tracking, and preview capabilities for natural language CAD operations.

## Core Components

### 1. Chat Interface Panel

**Purpose**: Primary input interface for natural language prompts and operation control.

**Layout**:
- Natural language input textarea (multi-line, expandable)
- Three action buttons: Parse, Preview, Apply
- Quick example prompts (clickable)
- Results display area (structured plan output)

**Behavior**:
- Parse button: Always enabled when text is present
- Preview button: Enabled only after successful parse
- Apply button: Enabled only after successful preview
- Example prompts: Click to populate input field
- Results area: Shows parsed plan structure, validation messages, errors

### 2. Action Log Panel

**Purpose**: Chronological record of all operations with detailed tracking and parameter editing.

**Entry Format**:
```
[Status Icon] [Operation Summary]
              [Details/Description]
              [Technical Operations Chain]
              [Editable Parameters] (when applicable)
              [Timestamp]
```

**Status Icons**:
- ✓ (Green): Successful operation
- ✗ (Red): Failed operation  
- ⚠ (Yellow): Warning/partial success
- ⏳ (Gray): In progress/pending

**Entry Types**:

1. **System Events**
   - Initialization, configuration changes, errors
   - Format: `System initialized` / `Settings updated` / `Connection lost`

2. **Parse Results**
   - Format: `Parsed: "natural language prompt"`
   - Details: Operation count, confidence score, warnings
   - Technical: `parse → validate → plan`

3. **Geometric Operations**
   - Format: `rectangle(100×50) → extrude(5mm)`
   - Details: Human-readable description
   - Technical: `create_sketch → draw_rectangle → extrude`
   - Parameters: Editable dimension inputs with units

4. **Feature Operations**
   - Format: `hole(⌀6mm) → pattern(4×corners)`
   - Details: Feature type, count, positioning
   - Technical: `create_hole → pattern_rectangular`

5. **Modifications**
   - Format: `fillet(R3mm) → 8 edges`
   - Details: Feature modified, scope
   - Technical: `select_edges → fillet → validate`

**Interactive Elements**:
- **Parameter Editing**: Inline input fields for dimensions
- **Re-execution**: Button to re-run operation with new parameters
- **Expand/Collapse**: Show/hide technical details
- **Copy/Export**: Copy operation details or export log

### 3. Preview Panel

**Purpose**: Visual and analytical preview of planned operations before execution.

**Components**:

1. **Before/After Images**
   - Side-by-side comparison views
   - Placeholder graphics when actual renders unavailable
   - Zoom/pan controls for detailed inspection

2. **Operation Summary**
   - Statistics: operation count, estimated time, confidence
   - Feature list: what will be created/modified
   - Timeline impact: where operations will appear

3. **Validation Warnings**
   - Geometric warnings (thin walls, small features)
   - Manufacturing warnings (tool limitations)
   - Design warnings (best practice violations)

### 4. Status Bar

**Purpose**: Global system status and connection information.

**Elements**:
- Processing indicator (spinner + status text)
- Connection status (LLM endpoint, local/cloud mode)
- Quick stats (operations today, success rate)

## Interaction Flows

### Primary Workflow

1. **Input Phase**
   - User enters natural language prompt
   - System validates input length/content
   - Parse button becomes enabled

2. **Parse Phase**
   - User clicks Parse button
   - System shows processing indicator
   - Results appear in both results area and action log
   - Preview button becomes enabled on success

3. **Preview Phase**
   - User clicks Preview button  
   - System generates sandbox preview
   - Preview panel updates with before/after comparison
   - Apply button becomes enabled on success

4. **Apply Phase**
   - User clicks Apply button
   - Confirmation dialog for destructive operations
   - System executes operations with progress tracking
   - Action log updates with real-time progress
   - Success/failure notification

### Error Handling

**Parse Errors**:
- Red status icon in action log
- Error details in results area
- Suggested corrections when possible
- Parse button remains enabled for retry

**Preview Errors**:
- Warning status icon (operation may still be viable)
- Detailed error explanation
- Option to proceed with warnings or modify plan

**Apply Errors**:
- Red status icon with rollback notification
- Full error details and recovery options
- Timeline state preserved (no partial applications)

### Parameter Editing

**Inline Editing**:
- Click dimension value to edit
- Input validation (positive numbers, reasonable ranges)
- Unit conversion support
- Real-time preview updates (when enabled)

**Batch Editing**:
- Select multiple parameters
- Apply changes to similar operations
- Undo/redo support

## Visual Design Guidelines

### Color Scheme

**Primary Colors**:
- Fusion Blue (#0696D7): Primary actions, links, highlights
- Success Green (#28a745): Successful operations, confirmations
- Warning Yellow (#ffc107): Warnings, cautions
- Error Red (#dc3545): Errors, destructive actions
- Neutral Gray (#6c757d): Secondary actions, disabled states

**Background Colors**:
- Panel Background: White (#ffffff)
- App Background: Light Gray (#f5f5f5)
- Input Backgrounds: Off-white (#f8f9fa)
- Code/Technical: Light Gray (#f8f9fa)

### Typography

**Fonts**:
- UI Text: Segoe UI, system fonts
- Code/Technical: Consolas, Monaco, monospace
- Dimensions: Tabular numbers preferred

**Sizes**:
- Headers: 18px (bold)
- Body Text: 14px
- Small Text: 12px
- Code Text: 12px
- Captions: 11px

### Spacing and Layout

**Grid System**:
- Base unit: 4px
- Standard spacing: 8px, 12px, 16px, 20px
- Panel padding: 20px
- Component gaps: 12px

**Responsive Breakpoints**:
- Desktop: > 768px (two-panel layout)
- Tablet/Mobile: ≤ 768px (single-panel, stacked)

## Accessibility Requirements

### Keyboard Navigation
- Tab order: Input → Parse → Preview → Apply → Log entries
- Enter key: Activate focused button
- Escape key: Cancel current operation
- Arrow keys: Navigate log entries

### Screen Reader Support
- Semantic HTML structure
- ARIA labels for status icons
- Live regions for status updates
- Alt text for preview images

### Color Accessibility
- WCAG AA contrast ratios
- Color-blind friendly palette
- Status conveyed through icons + color
- High contrast mode support

## Performance Considerations

### Optimization Targets
- Initial load: < 500ms
- Parse response: < 2s
- Preview generation: < 5s
- Log entry rendering: < 100ms

### Data Management
- Log entry limit: 100 visible entries
- Automatic cleanup of old entries
- Efficient DOM updates (virtual scrolling for large logs)
- Debounced parameter updates

### Memory Usage
- Preview image caching (last 5 previews)
- Lazy loading of historical log entries
- Cleanup of temporary preview data

## Integration Points

### Fusion 360 Integration
- Palette docking (right panel default)
- Theme synchronization with Fusion
- Keyboard shortcut registration
- Timeline integration for feature mapping

### LLM Service Integration
- Request/response format specification
- Error handling for service unavailability
- Timeout and retry logic
- Progress tracking for long operations

### Action Log Persistence
- Local storage for session continuity
- Export formats (JSON, CSV, TXT)
- Import capability for replay
- Backup and recovery

## Testing Requirements

### Unit Tests
- Component rendering
- User interaction handling
- Data transformation
- Error state management

### Integration Tests
- End-to-end workflow
- LLM service communication
- Fusion 360 API integration
- Cross-browser compatibility

### Usability Tests
- First-time user experience
- Expert user efficiency
- Error recovery scenarios
- Accessibility compliance

## Future Enhancements

### Phase 2 Features
- Drag-and-drop parameter reordering
- Visual operation timeline
- Collaborative features (shared logs)
- Advanced preview rendering

### Phase 3 Features
- Voice input support
- Gesture control (touch devices)
- AI-powered operation suggestions
- Custom UI themes

---

## Implementation Notes

### Framework Considerations
- Pure HTML/CSS/JS for maximum compatibility
- Progressive enhancement approach
- Minimal external dependencies
- Fusion 360 webview compatibility

### Development Workflow
1. Static mockup (HTML/CSS)
2. Interactive prototype (JS)
3. Fusion integration layer
4. Backend service integration
5. Testing and refinement

### Deployment Strategy
- Embedded in Fusion add-in package
- Local file serving (no external CDNs)
- Version management with add-in updates
- Backward compatibility for settings/logs
