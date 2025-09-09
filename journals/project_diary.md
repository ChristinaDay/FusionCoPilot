## Fusion Co‑Pilot – Project Diary

### 2025-09-09
- **Add‑in startup fixed**: Resolved resourceFolder and htmlFileURL issues.
  - Removed/standardized icon resource paths and created `fusion_addin/resources/commandIcons`.
  - Added a real `fusion_addin/icon.png` for manifest `iconFilename`.
  - Wrote palette HTML to `fusion_addin/resources/palette/index.html` and passed a proper `file:///` URL to `palettes.add(...)`.
  - Added startup breadcrumbs to aid future debugging.
- **Template cleanup**: Moved duplicate scaffolds to `fusion_addin/_templates/` so Fusion only loads the primary add‑in.
- **Repo setup**: Initialized git, added comprehensive `.gitignore`, and pushed to GitHub `origin` main.
  - Remote: `https://github.com/ChristinaDay/FusionCoPilot.git`
- **Current state**: Add‑in loads; palette opens successfully.

### Next Candidates
- Wire Parse/Preview/Apply buttons to real handlers.
- Add LLM health‑check and stub fallback.
- Implement a minimal execution demo (e.g., create parametric box).
- Improve error surfacing in‑palette and expand tests with CI.


