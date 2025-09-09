# Fusion 360 Co-Pilot Beta Installation Guide

Welcome to the Fusion 360 Co-Pilot beta testing program! This guide will walk you through the complete installation and setup process.

**⚠️ Beta Software Notice**: This is pre-release software for testing purposes only. Please backup your important Fusion 360 data before installation.

---

## 📋 Pre-Installation Checklist

### **System Requirements**
- ✅ **Fusion 360**: Version 2.0.15000 or later (latest recommended)
- ✅ **Operating System**: 
  - Windows 10/11 (64-bit)
  - macOS 10.15 Catalina or later
  - Linux (Ubuntu 20.04+ experimental support)
- ✅ **RAM**: 8GB minimum, 16GB recommended
- ✅ **Storage**: 500MB free space for add-in and logs
- ✅ **Internet**: Required for LLM API access
- ✅ **Permissions**: Admin rights for installation

### **Prerequisites**
- ✅ **Python 3.8+**: Required for LLM service (check: `python3 --version`)
- ✅ **Fusion 360 Add-ins Enabled**: Settings → General → API
- ✅ **LLM API Access**: OpenAI, Anthropic, or Azure OpenAI account

---

## 📦 Installation Steps

### **Step 1: Download Beta Package**

You should have received:
- **`fusion-copilot-beta.zip`** - Main installation package
- **`BETA_API_KEY.txt`** - Your test API key (if provided)
- **`BETA_CONFIG.yaml`** - Pre-configured settings

**File verification:**
```bash
# Verify download integrity (optional)
# SHA256 checksums will be provided via email
```

### **Step 2: Extract and Prepare Files**

1. **Create installation directory:**
   ```bash
   # Windows
   mkdir "C:\Users\%USERNAME%\Documents\FusionCoPilotBeta"
   
   # macOS/Linux  
   mkdir ~/Documents/FusionCoPilotBeta
   ```

2. **Extract beta package:**
   - Extract `fusion-copilot-beta.zip` to the installation directory
   - Verify all files are present (see file list below)

3. **Expected file structure:**
   ```
   FusionCoPilotBeta/
   ├── fusion_addin/           # Main add-in code
   │   ├── main.py
   │   ├── ui.py
   │   ├── executor.py
   │   ├── sanitizer.py
   │   ├── llm_service.py
   │   ├── env_config.py
   │   ├── action_log.py
   │   ├── manifest.json
   │   ├── settings.yaml
   │   ├── plan_schema.json
   │   └── .env.template
   ├── BETA_INSTALL.md         # This file
   ├── BETA_TESTING.md         # Testing guide
   ├── BETA_SCENARIOS.json     # Test scenarios
   └── BETA_SUPPORT.md         # Support contacts
   ```

### **Step 3: Configure API Access**

#### **Option A: Using Provided Test Key**
If you received `BETA_API_KEY.txt`:
1. Copy `.env.template` to `.env` in the `fusion_addin/` directory
2. Edit `.env` and paste your provided API key
3. Set environment to `COPILOT_ENVIRONMENT=beta`

#### **Option B: Using Your Own API Key**
If using your own OpenAI/Anthropic key:

1. **OpenAI Setup:**
   ```bash
   # Copy template
   cp fusion_addin/.env.template fusion_addin/.env
   
   # Edit .env file and add:
   OPENAI_API_KEY=sk-your_openai_key_here
   COPILOT_LLM_PROVIDER=openai
   COPILOT_LLM_MODEL=gpt-4
   COPILOT_ENVIRONMENT=beta
   ```

2. **Anthropic Setup:**
   ```bash
   # Edit .env file and add:
   ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
   COPILOT_LLM_PROVIDER=anthropic
   COPILOT_LLM_MODEL=claude-3-5-sonnet-20241022
   COPILOT_ENVIRONMENT=beta
   ```

#### **Configuration Validation**
```bash
cd fusion_addin
python3 -c "from env_config import get_environment_config; print(get_environment_config().validate_configuration())"
```

Expected output: `{'valid': True, 'warnings': [], 'errors': [], ...}`

### **Step 4: Install Python Dependencies**

The beta version requires some Python packages:

```bash
# Navigate to fusion_addin directory
cd fusion_addin

# Install required packages
pip3 install requests pyyaml

# Optional: Install for advanced features
pip3 install flask flask-cors  # For local LLM stub
```

**Note**: If you don't have pip, install Python from python.org first.

### **Step 5: Install Fusion 360 Add-in**

#### **Method A: Using Fusion 360 UI (Recommended)**

1. **Open Fusion 360**
2. **Navigate to Add-ins**: Tools → Add-Ins
3. **Add from folder**: Click "+" next to "My Add-Ins" 
4. **Select folder**: Browse to `FusionCoPilotBeta/fusion_addin/`
5. **Enable add-in**: Check the box next to "Fusion 360 Co-Pilot Beta"
6. **Run add-in**: Click "Run" to start

#### **Method B: Manual Installation**

1. **Find Fusion 360 Add-ins folder:**
   ```bash
   # Windows
   %APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\
   
   # macOS
   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/
   ```

2. **Create symbolic link or copy:**
   ```bash
   # Windows (as Administrator)
   mklink /D "FusionCoPilotBeta" "C:\Users\%USERNAME%\Documents\FusionCoPilotBeta\fusion_addin"
   
   # macOS/Linux
   ln -s ~/Documents/FusionCoPilotBeta/fusion_addin ./FusionCoPilotBeta
   ```

3. **Restart Fusion 360** and enable the add-in

### **Step 6: Verify Installation**

#### **Visual Verification**
After enabling the add-in, you should see:
- ✅ **Co-Pilot Panel**: New panel in the Fusion 360 UI
- ✅ **Toolbar Button**: Co-Pilot icon in the toolbar
- ✅ **Menu Items**: Co-Pilot commands in the Tools menu

#### **Functional Test**
1. **Open the Co-Pilot panel**
2. **Enter test prompt**: "Create a simple 10x10x5mm cube"
3. **Click Parse**: Should generate a plan with 3 operations
4. **Click Preview**: Should show operation details
5. **Click Apply**: Should create a cube in Fusion 360

#### **Error Diagnosis**
If the test fails, check:

```python
# Run diagnostics in Fusion 360 Python console
import sys
sys.path.append('/path/to/fusion_addin')

from env_config import get_environment_config
config = get_environment_config()
print(config.validate_configuration())

from llm_service import create_llm_service
import yaml
with open('settings.yaml', 'r') as f:
    settings = yaml.safe_load(f)
llm = create_llm_service(settings)
print(llm.health_check())
```

---

## ⚙️ Beta Configuration

### **Beta-Specific Settings**

Your installation includes special beta configurations in `settings.yaml`:

```yaml
# Beta Testing Configuration
beta_testing:
  enabled: true
  participant_id: "beta_user_001"
  feedback_collection: true
  detailed_logging: true
  performance_metrics: true

# Enhanced Logging for Beta
logging:
  level: "DEBUG"
  max_log_size: 50  # Larger log files
  beta_session_logs: true

# Beta Safety Features  
security:
  confirm_destructive: true
  beta_warnings: true
  
# Performance Monitoring
advanced:
  performance_monitoring: true
  beta_telemetry: true
```

### **Test Data Collection**

The beta version automatically collects (with your permission):
- **Usage Patterns**: Which features are used most
- **Performance Metrics**: Response times, success rates
- **Error Logs**: For debugging and improvement
- **Feedback Data**: From your testing activities

**Privacy**: No CAD model data or personal information is transmitted.

---

## 🧪 Post-Installation Testing

### **Basic Functionality Test**

Complete this test sequence after installation:

#### **Test 1: Simple Geometry**
```
Prompt: "Create a rectangular plate 50x30x5mm"
Expected: 3 operations (sketch, rectangle, extrude)
Result: ✅ Pass / ❌ Fail
```

#### **Test 2: Complex Features**
```  
Prompt: "Add 4 holes 6mm diameter, 10mm from edges"
Expected: 4-6 operations (sketch, circles, pattern, cut)
Result: ✅ Pass / ❌ Fail
```

#### **Test 3: Error Handling**
```
Prompt: "Create something impossible"  
Expected: Error message with suggestions
Result: ✅ Pass / ❌ Fail
```

#### **Test 4: Performance**
```
Prompt: "Create a complex bracket with holes and fillets"
Expected: Response in <10 seconds
Result: ✅ Pass / ❌ Fail
```

### **Advanced Feature Test**

#### **Test 5: LLM Integration**
```
Change LLM provider in .env file and restart
Test with different models (GPT-4, Claude)
Expected: Consistent results across providers
Result: ✅ Pass / ❌ Fail
```

#### **Test 6: Action Logging**
```
Create several parts, check action logs
Navigate to logs/actions directory
Expected: Detailed JSON logs of all operations
Result: ✅ Pass / ❌ Fail
```

---

## 🔧 Troubleshooting

### **Common Issues**

#### **"Add-in not appearing"**
**Causes & Solutions:**
- ✅ Check Fusion 360 API enabled: Settings → General → API
- ✅ Verify file permissions: Add-in files must be readable
- ✅ Restart Fusion 360 after installation
- ✅ Check add-in path is correct

#### **"API key not working"**
**Causes & Solutions:**
- ✅ Verify API key format and validity
- ✅ Check internet connectivity
- ✅ Ensure correct provider selected
- ✅ Test key with curl or online tools

#### **"Python import errors"**
**Causes & Solutions:**
- ✅ Install required packages: `pip3 install requests pyyaml`
- ✅ Check Python version: `python3 --version`
- ✅ Verify Python path in system
- ✅ Try reinstalling dependencies

#### **"LLM requests failing"**
**Causes & Solutions:**
- ✅ Check API rate limits
- ✅ Verify endpoint URLs
- ✅ Test network connectivity
- ✅ Review error logs

### **Debug Mode**

Enable detailed logging for troubleshooting:

1. **Edit settings.yaml:**
   ```yaml
   logging:
     debug: true
     level: "DEBUG"
   ```

2. **Check log files:**
   ```bash
   # Navigate to logs directory
   cd fusion_addin/logs/
   
   # View latest debug log
   tail -f copilot_debug.log
   ```

3. **Run diagnostic script:**
   ```bash
   cd fusion_addin
   python3 -c "
   import sys, traceback
   try:
       from main import run_tests
       run_tests()
   except Exception as e:
       print(f'Error: {e}')
       traceback.print_exc()
   "
   ```

### **Getting Help**

#### **Self-Service**
1. **Check logs**: `fusion_addin/logs/copilot_debug.log`
2. **Validate config**: Run configuration validation script
3. **Review documentation**: Read through setup steps again
4. **Test components**: Use diagnostic scripts provided

#### **Beta Support**
- **Email**: beta-support@fusioncopilot.dev
- **Response Time**: 24 hours on weekdays
- **Include**: Log files, error messages, system info

**Email Template:**
```
Subject: Beta Installation Issue - [Your Name]

Issue Description:
[Describe what's not working]

Steps Taken:
[What you've tried so far]

System Information:
- OS: [Windows 11 / macOS 12 / etc.]
- Fusion 360 Version: [2.0.xxxxx]
- Python Version: [3.x.x]

Error Messages:
[Copy exact error text]

Attachments:
- copilot_debug.log
- .env file (with API keys redacted)
```

---

## 🔄 Updates and Maintenance

### **Beta Update Process**

During the beta period, you may receive updates:

1. **Notification**: Email with update package
2. **Backup**: Save your current `.env` and any custom settings
3. **Installation**: Follow same installation steps with new package
4. **Migration**: Restore your configuration files
5. **Testing**: Run post-installation tests

### **Configuration Backup**

Before any updates, backup these files:
```bash
cp fusion_addin/.env fusion_addin/.env.backup
cp fusion_addin/settings.yaml fusion_addin/settings.yaml.backup
cp -r fusion_addin/logs/ fusion_addin/logs.backup/
```

### **Uninstallation**

If you need to remove the beta:

1. **Disable in Fusion 360**: Uncheck in Add-Ins dialog
2. **Remove files**: Delete installation directory
3. **Clean registry** (Windows): Remove any registry entries
4. **Revoke API keys**: Disable test keys if provided

---

## 📊 Success Metrics

### **Installation Success Indicators**
- ✅ All test scenarios pass
- ✅ No error messages during setup
- ✅ Co-Pilot UI appears correctly
- ✅ LLM integration working
- ✅ Action logging functional

### **Performance Benchmarks**
- ⚡ Response time: <5 seconds for simple prompts
- ⚡ Success rate: >80% for standard operations
- ⚡ Memory usage: <200MB additional RAM
- ⚡ Startup time: <3 seconds to initialize

### **Ready for Testing**
When you can successfully:
- Create geometry from natural language
- Preview operations before execution
- Handle errors gracefully
- Access all UI features
- Generate action logs

---

## 🎉 Next Steps

### **After Successful Installation**

1. **Complete Beta Onboarding**: Fill out the beta tester profile
2. **Join Beta Community**: Access to Discord/Slack channel
3. **Schedule Check-in**: 15-minute call with dev team
4. **Begin Testing**: Start with provided test scenarios
5. **Provide Feedback**: Daily usage logs and weekly forms

### **Beta Testing Resources**

- 📖 **BETA_TESTING.md**: Complete testing guide and scenarios
- 📝 **Feedback Forms**: Weekly survey links
- 💬 **Support Channel**: Direct access to development team
- 📊 **Progress Tracking**: Your testing contribution dashboard

---

**Installation Complete?**

**Next**: Read `BETA_TESTING.md` and start your testing journey!

**Questions?** Contact: beta-support@fusioncopilot.dev

---

*Fusion 360 Co-Pilot Beta Installation Guide v1.0*  
*Last Updated: 2024-09-09*  
*Valid for Beta Version: 1.0.0-beta*