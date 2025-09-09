# Fusion 360 Natural-Language CAD Co-Pilot Add-in

## Installation Instructions

### Method 1: Fusion 360 Scripts & Add-Ins (Recommended)
1. **Open Fusion 360**
2. Navigate to **Tools → Scripts and Add-Ins**
3. Click the **Add-Ins** tab
4. Click the **+** (green plus) button
5. Browse to and select this `fusion_addin` folder
6. Click **Run** to activate the Co-Pilot
7. The **CoPilot** button will appear in the **Solid → Create** panel

Note: When selecting the folder, verify the entry file is `fusion_addin.py` and the manifest is `fusion_addin.manifest`.

### Method 2: Manual Installation
1. Copy this entire `fusion_addin` folder to:
   - **Windows**: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`
   - **macOS**: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`
2. Restart Fusion 360
3. Enable the add-in via **Tools → Scripts and Add-Ins**

## First Launch

1. Click the **CoPilot** button in the toolbar
2. The Co-Pilot panel will open on the right side
3. Configure your LLM endpoint in `settings.yaml` if needed
4. Start with a simple prompt like: "Create a 50mm cube"

## Features

- **Natural Language Parsing**: Convert plain English to structured CAD operations
- **Safe Preview**: Test operations in sandbox before applying to your design  
- **Action Logging**: Complete audit trail of all operations with timeline mapping
- **Transaction Safety**: Full rollback capability if operations fail
- **Configurable LLM**: Use local stub or connect to your preferred LLM service

## Troubleshooting

**Add-in won't load:**
- Check that Python 3.10+ is available in Fusion 360
- Verify all files are present in the add-in folder
- Ensure only one manifest is present (we ship just `fusion_addin.manifest`)
- Check the Fusion 360 console for error messages

**CoPilot button missing:**
- Ensure add-in is enabled in Scripts & Add-Ins
- Try restarting Fusion 360
- Check that you're in the Design workspace

**LLM connection errors:**
- Verify `settings.yaml` has correct endpoint URL
- For development, ensure stub server is running: `python ../llm_stub/server.py`
- Check firewall settings for localhost connections

## Support

- See main README.md for comprehensive documentation
- Check action logs for detailed operation history
- Enable debug mode in `settings.yaml` for detailed logging
