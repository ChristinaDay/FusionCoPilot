# Changelog

All notable changes to the Fusion 360 Natural-Language CAD Co-Pilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial development pack release
- Natural language to CAD operation parsing
- Structured plan validation and sanitization
- Sandbox preview system for safe operation testing
- Comprehensive action logging with timeline mapping
- Local LLM stub server for development
- Unit test suite for core validation logic
- HTML mockup for UI prototyping
- Extensive documentation and examples

### Security
- Local-only processing mode for enterprise environments
- No geometry data transmission to external services
- Configurable LLM endpoints with full user control

## [0.1.0-dev] - 2024-01-XX

### Added
- Core add-in structure with Fusion 360 integration
- Basic UI components (chat panel, preview, action log)
- Plan schema definition with JSON Schema validation
- Sanitizer with unit conversion and safety checks
- Executor with deterministic Fusion API mapping
- Action log persistence and export functionality
- Development tools and CI test runner
- 20+ sample prompts with expected outputs

### Technical Details
- Python 3.10+ compatibility
- Fusion 360 2023.1+ support
- MIT license for open development
- PEP8 compliant code with comprehensive docstrings
- Pytest-based unit testing framework

### Development Infrastructure
- Local stub server for offline development
- Mock UI for rapid prototyping
- Test fixture generation tools
- Automated CI testing pipeline
- Comprehensive error handling and user feedback

---

## Development Notes

### Version Strategy
- **0.x.x-dev**: Development and testing versions
- **1.0.0**: First stable release for Autodesk Marketplace
- **1.x.x**: Feature releases with backward compatibility
- **2.0.0+**: Major releases with potential breaking changes

### Release Process
1. Update version in `manifest.json`
2. Update this CHANGELOG.md
3. Run full test suite (`pytest`)
4. Generate new dev pack (`./pack.sh`)
5. Test installation in clean Fusion environment
6. Tag release in version control

### Planned Features for v1.0
- [ ] Advanced geometry recognition
- [ ] Multi-step operation chaining
- [ ] Custom operation templates
- [ ] Enhanced error recovery
- [ ] Performance optimizations
- [ ] Comprehensive user documentation
- [ ] Video tutorial series

### Known Issues
- Preview system requires active document
- Large plans (>50 operations) may impact performance
- Some complex geometry references need manual clarification
- Unit conversion edge cases in mixed-unit documents

### Breaking Changes Policy
Breaking changes will be clearly documented and include:
- Migration guides for existing action logs
- Backward compatibility shims where possible
- Clear deprecation warnings in advance
- Support for legacy plan formats during transition periods
