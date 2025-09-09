# Fusion 360 Natural-Language CAD Co-Pilot

A comprehensive Fusion 360 add-in that transforms natural language descriptions into precise CAD operations using structured LLM planning and deterministic execution.

## 🚀 Overview

This Co-Pilot bridges the gap between natural language intent and CAD precision by:
- **Parsing** natural language into structured, validated plans
- **Previewing** operations in a sandbox before applying to your design
- **Executing** plans with full transaction safety and rollback capability
- **Logging** all actions with timeline mapping for complete auditability

## 📋 Prerequisites

- **Fusion 360** (2023.1 or later recommended)
- **Python 3.10+** (bundled with Fusion 360)
- **Node.js 16+** (optional, for local LLM stub server)

## 🛠 Installation

### 1. Extract the Dev Pack
```bash
# Extract the fusion-copilot-devpack.zip to your local drive
unzip fusion-copilot-devpack.zip
cd fusion-copilot-devpack
```

### 2. Install Fusion 360 Add-in
1. Open **Fusion 360**
2. Navigate to **Tools → Scripts and Add-Ins**
3. Click **Add-Ins** tab, then **+** (green plus icon)
4. Browse to and select the `fusion_addin` folder
5. Click **Run** to activate the Co-Pilot

### 3. Configure LLM Endpoint (Optional)
Edit `fusion_addin/settings.yaml` to configure your LLM endpoint:
```yaml
llm_endpoint: "http://localhost:8080/llm"  # Default local stub
local_mode: true  # Set to false for production LLM
```

### 4. Start Local LLM Stub (Development)
For development and testing without external LLM dependencies:
```bash
cd llm_stub
python server.py  # or: node server.js
# Server runs on http://localhost:8080
```

## 🎯 Quick Start

### Basic Usage Workflow
1. **Launch Co-Pilot**: In Fusion 360, click the **CoPilot** button in the toolbar
2. **Enter Prompt**: Type natural language like "Create a 50x30mm plate with 4 corner holes"
3. **Parse**: Click **Parse** to convert to structured plan
4. **Preview**: Click **Preview** to simulate in sandbox (safe, non-destructive)
5. **Inspect**: Review the action log and modify parameters if needed
6. **Apply**: Click **Apply** to execute on your active design
7. **Export**: Export action log for documentation or replay

### Example Prompts
- "Extrude this sketch 10mm upward"
- "Create a linear pattern of 5 holes spaced 20mm apart"
- "Fillet all edges with 3mm radius"
- "Shell this body with 2mm wall thickness"
- "Mirror this feature across the YZ plane"

## 🧪 Development & Testing

### Run Tests
```bash
# Install test dependencies (if needed)
pip install pytest jsonschema

# Run unit tests
pytest fusion_addin/tests/
```

### Generate Test Fixtures
```bash
python dev_tools/generate_test_fixtures.py
```

### Run CI Tests
```bash
./dev_tools/ci_test_runner.sh
```

## 🔧 Configuration Options

### `settings.yaml` Parameters
- `llm_endpoint`: URL of your LLM service
- `local_mode`: Use local stub server (true) or external LLM (false)
- `machine_profile`: Manufacturing constraints (tool diameters, material limits)
- `units_default`: Default units (mm or inches)
- `max_operations_per_plan`: Safety limit for plan complexity

### Machine Profile Example
```yaml
machine_profile:
  min_tool_diameter: 0.5  # mm
  max_cut_depth: 100      # mm
  supported_materials: ["aluminum", "steel", "plastic"]
```

## 📊 Action Log & Export

The Co-Pilot maintains a complete audit trail:
- **Timestamped entries** for every applied plan
- **Timeline node mapping** to Fusion features
- **Parameter tracking** with before/after values
- **Export formats**: JSON, TXT, CSV
- **Replay capability** for reproducing operations

### Export Action Log
```python
from fusion_addin.action_log import export_action_log
export_action_log(format='json', filename='my_session.json')
```

## 🔒 Security & Privacy

### Enterprise/Local Mode
For proprietary designs, enable local-only processing:
1. Set `local_mode: true` in `settings.yaml`
2. Deploy your own LLM endpoint (no cloud calls)
3. All processing happens locally - no geometry data leaves your network

### Data Handling
- **No geometry export**: Only operation parameters are sent to LLM
- **Configurable endpoints**: Full control over where requests go
- **Action log encryption**: Optional encryption for sensitive logs

## 🐛 Troubleshooting

### Common Issues

**"Unit mismatch detected"**
- Solution: Check your document units vs. prompt units. Use explicit units like "10mm" or "0.5in"

**"Feature not found - ambiguous reference"**
- Solution: Be more specific in prompts. Use feature names or geometric descriptions

**"LLM endpoint unreachable"**
- Solution: Ensure stub server is running (`python llm_stub/server.py`) or check `llm_endpoint` in settings

**"Plan validation failed"**
- Solution: Check the action log for specific validation errors. Common issues: negative dimensions, missing references

**"Transaction rollback occurred"**
- Solution: Check Fusion timeline for conflicts. Some operations may require specific feature states

### Debug Mode
Enable detailed logging by setting `debug: true` in `settings.yaml`. Logs are written to `%TEMP%/fusion_copilot_debug.log`.

## 🏗 Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Natural       │    │   Structured     │    │   Fusion API    │
│   Language      │───▶│   Plan JSON      │───▶│   Operations    │
│   Prompt        │    │   (Validated)    │    │   (Transacted)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Service   │    │   Sanitizer +    │    │   Action Log    │
│   (Configurable)│    │   Validator      │    │   (Persistent)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components
- **`main.py`**: Add-in lifecycle and UI integration
- **`ui.py`**: Chat interface and preview panels  
- **`sanitizer.py`**: Input validation and safety checks
- **`executor.py`**: Deterministic Fusion API execution
- **`action_log.py`**: Audit trail and replay system

## 🚀 Next Steps for Production

### Development Roadmap
- [ ] **Enhanced LLM Integration**: Add support for OpenAI, Anthropic, Azure OpenAI
- [ ] **Advanced Geometry Recognition**: Computer vision for "select this feature" prompts
- [ ] **Collaborative Features**: Multi-user action logs and shared templates
- [ ] **Performance Optimization**: Batch operations and async execution
- [ ] **Advanced Validation**: FEA-aware constraints and manufacturability checks

### Autodesk Marketplace Submission Checklist
- [ ] **Code Signing**: Sign add-in with Autodesk certificate
- [ ] **Security Review**: Complete Autodesk security questionnaire
- [ ] **Documentation**: Create user manual and video tutorials
- [ ] **Testing**: Comprehensive testing across Fusion versions
- [ ] **Licensing**: Implement license validation system
- [ ] **Localization**: Support for multiple languages
- [ ] **Analytics**: Usage tracking and error reporting
- [ ] **Support System**: Help documentation and contact methods

### Enterprise Deployment
- [ ] **SSO Integration**: Active Directory/SAML authentication
- [ ] **Audit Compliance**: SOX/ISO compliance for action logs
- [ ] **Custom LLM Endpoints**: Integration with enterprise AI platforms
- [ ] **Batch Processing**: Command-line tools for automated workflows
- [ ] **API Extensions**: REST API for external system integration

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/fusion-copilot/issues)
- **Documentation**: [Wiki](https://github.com/your-org/fusion-copilot/wiki)
- **Community**: [Discussions](https://github.com/your-org/fusion-copilot/discussions)

---

**Note**: This is a development pack. For production use, review security settings, configure proper LLM endpoints, and follow your organization's CAD data handling policies.
