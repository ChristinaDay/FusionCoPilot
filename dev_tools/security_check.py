#!/usr/bin/env python3
"""
Fusion 360 Co-Pilot Security Validation Script

This script performs automated security checks on the codebase to ensure
production readiness and compliance with security best practices.

Usage:
    python security_check.py [--verbose] [--fix]

Author: Fusion CoPilot Team
License: MIT
"""

import os
import re
import json
import sys
import argparse
from typing import List, Dict, Tuple, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "fusion_addin"))

try:
    from env_config import get_environment_config
    ENV_CONFIG_AVAILABLE = True
except ImportError:
    ENV_CONFIG_AVAILABLE = False


class SecurityChecker:
    """Automated security validation for Fusion 360 Co-Pilot."""
    
    def __init__(self, project_root: str, verbose: bool = False):
        self.project_root = Path(project_root)
        self.verbose = verbose
        self.issues = []
        self.warnings = []
        self.info = []
        
    def log(self, level: str, message: str, file_path: str = None):
        """Log a security finding."""
        finding = {
            'level': level,
            'message': message,
            'file': file_path
        }
        
        if level == 'ERROR':
            self.issues.append(finding)
        elif level == 'WARNING':
            self.warnings.append(finding)
        else:
            self.info.append(finding)
            
        if self.verbose:
            prefix = f"[{level}]"
            if file_path:
                prefix += f" {file_path}"
            print(f"{prefix}: {message}")
    
    def check_hardcoded_secrets(self) -> None:
        """Check for hardcoded API keys, passwords, and secrets."""
        print("🔍 Checking for hardcoded secrets...")
        
        # Patterns that indicate potential secrets
        secret_patterns = [
            (r'api[_-]?key\s*[=:]\s*["\'][^"\']{20,}["\']', 'API key'),
            (r'password\s*[=:]\s*["\'][^"\']+["\']', 'Password'),
            (r'secret\s*[=:]\s*["\'][^"\']{10,}["\']', 'Secret'),
            (r'token\s*[=:]\s*["\'][^"\']{20,}["\']', 'Token'),
            (r'sk-[A-Za-z0-9]{20,}', 'OpenAI API key'),
            (r'xoxb-[0-9]{10,}-[0-9]{10,}-[A-Za-z0-9]{20,}', 'Slack token'),
            (r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'UUID/GUID'),
        ]
        
        python_files = self.project_root.rglob("*.py")
        yaml_files = self.project_root.rglob("*.yaml")
        json_files = self.project_root.rglob("*.json")
        
        for file_path in list(python_files) + list(yaml_files) + list(json_files):
            # Skip test files and examples
            if 'test' in str(file_path).lower() or 'example' in str(file_path).lower():
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                for pattern, secret_type in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip obvious placeholders
                        matched_text = match.group()
                        if any(placeholder in matched_text.lower() for placeholder in [
                            'your_', 'placeholder', 'example', 'dummy', 'test',
                            'fake', 'sample', 'template', 'xxx', '***'
                        ]):
                            continue
                            
                        self.log('ERROR', f"Potential {secret_type} found: {matched_text[:50]}...", 
                                str(file_path.relative_to(self.project_root)))
                                
            except Exception as e:
                self.log('WARNING', f"Could not scan file: {e}", str(file_path.relative_to(self.project_root)))
    
    def check_network_security(self) -> None:
        """Check network security practices."""
        print("🌐 Checking network security...")
        
        python_files = self.project_root.rglob("*.py")
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for HTTP URLs (should be HTTPS)
                http_pattern = r'http://[^\s"\']*'
                http_matches = re.finditer(http_pattern, content)
                for match in http_matches:
                    url = match.group()
                    if 'localhost' not in url and '127.0.0.1' not in url:
                        self.log('WARNING', f"HTTP URL found (should use HTTPS): {url}",
                                str(file_path.relative_to(self.project_root)))
                
                # Check for disabled SSL verification
                ssl_disable_patterns = [
                    r'verify\s*=\s*False',
                    r'ssl_verify\s*=\s*False',
                    r'CERT_NONE',
                ]
                
                for pattern in ssl_disable_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        self.log('ERROR', f"SSL verification disabled: {match.group()}",
                                str(file_path.relative_to(self.project_root)))
                
            except Exception as e:
                self.log('WARNING', f"Could not scan file: {e}", str(file_path.relative_to(self.project_root)))
    
    def check_input_validation(self) -> None:
        """Check for input validation practices."""
        print("🛡️ Checking input validation...")
        
        python_files = self.project_root.rglob("*.py")
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for dangerous functions
                dangerous_functions = ['eval', 'exec', 'compile', '__import__']
                
                for func in dangerous_functions:
                    pattern = rf'\b{func}\s*\('
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.log('ERROR', f"Dangerous function used: {func}()",
                                str(file_path.relative_to(self.project_root)))
                
                # Check for SQL injection patterns
                sql_patterns = [
                    r'\.format\s*\([^)]*\+[^)]*\)',
                    r'%\s*\([^)]*\+[^)]*\)',
                    r'"[^"]*\+[^"]*"',
                ]
                
                for pattern in sql_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        if 'sql' in content.lower() or 'query' in content.lower():
                            self.log('WARNING', f"Potential SQL injection risk: {match.group()}",
                                    str(file_path.relative_to(self.project_root)))
                
            except Exception as e:
                self.log('WARNING', f"Could not scan file: {e}", str(file_path.relative_to(self.project_root)))
    
    def check_logging_security(self) -> None:
        """Check logging practices for security."""
        print("📝 Checking logging security...")
        
        python_files = self.project_root.rglob("*.py")
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for logging of sensitive data
                sensitive_log_patterns = [
                    r'log[^(]*\([^)]*password[^)]*\)',
                    r'log[^(]*\([^)]*api_key[^)]*\)',
                    r'log[^(]*\([^)]*secret[^)]*\)',
                    r'log[^(]*\([^)]*token[^)]*\)',
                    r'print\([^)]*password[^)]*\)',
                    r'print\([^)]*api_key[^)]*\)',
                ]
                
                for pattern in sensitive_log_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        self.log('WARNING', f"Potential sensitive data logging: {match.group()[:100]}",
                                str(file_path.relative_to(self.project_root)))
                
            except Exception as e:
                self.log('WARNING', f"Could not scan file: {e}", str(file_path.relative_to(self.project_root)))
    
    def check_environment_config(self) -> None:
        """Check environment configuration security."""
        print("⚙️ Checking environment configuration...")
        
        if not ENV_CONFIG_AVAILABLE:
            self.log('WARNING', "Environment configuration module not available")
            return
        
        try:
            env_config = get_environment_config(str(self.project_root / "fusion_addin"))
            status = env_config.validate_configuration()
            
            if not status['valid']:
                for error in status['errors']:
                    self.log('ERROR', f"Environment configuration error: {error}")
            
            for warning in status['warnings']:
                self.log('WARNING', f"Environment configuration warning: {warning}")
            
            # Check for .env files that shouldn't be committed
            env_files = list(self.project_root.rglob(".env"))
            for env_file in env_files:
                if env_file.name != '.env.template':
                    self.log('ERROR', f".env file found - should not be in version control: {env_file}")
            
        except Exception as e:
            self.log('WARNING', f"Environment configuration check failed: {e}")
    
    def check_file_permissions(self) -> None:
        """Check file permissions and ownership."""
        print("🔐 Checking file permissions...")
        
        sensitive_files = [
            ".env",
            "settings.yaml",
            "*.key",
            "*.pem",
            "*.p12",
            "*.pfx",
        ]
        
        for pattern in sensitive_files:
            files = self.project_root.rglob(pattern)
            for file_path in files:
                try:
                    stat = file_path.stat()
                    mode = oct(stat.st_mode)[-3:]
                    
                    # Check if file is readable by others
                    if mode[2] in ['4', '5', '6', '7']:
                        self.log('WARNING', f"Sensitive file readable by others: {file_path} ({mode})")
                    
                    # Check if file is writable by others
                    if mode[2] in ['2', '3', '6', '7']:
                        self.log('ERROR', f"Sensitive file writable by others: {file_path} ({mode})")
                        
                except Exception as e:
                    self.log('WARNING', f"Could not check permissions for {file_path}: {e}")
    
    def check_dependencies(self) -> None:
        """Check for known security vulnerabilities in dependencies."""
        print("📦 Checking dependencies...")
        
        # Look for requirements files
        req_files = list(self.project_root.rglob("requirements*.txt"))
        req_files.extend(self.project_root.rglob("Pipfile"))
        req_files.extend(self.project_root.rglob("pyproject.toml"))
        
        if not req_files:
            self.log('WARNING', "No dependency files found")
            return
        
        # Basic check for outdated or risky packages
        risky_packages = [
            'pickle',      # Arbitrary code execution
            'eval',        # Code injection
            'subprocess',  # Command injection risk if misused
        ]
        
        for req_file in req_files:
            try:
                content = req_file.read_text()
                for package in risky_packages:
                    if package in content:
                        self.log('WARNING', f"Potentially risky package: {package}",
                                str(req_file.relative_to(self.project_root)))
                        
            except Exception as e:
                self.log('WARNING', f"Could not scan dependency file {req_file}: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive security report."""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        
        # Determine overall security status
        if total_issues == 0 and total_warnings == 0:
            status = "✅ EXCELLENT"
        elif total_issues == 0 and total_warnings <= 3:
            status = "✅ GOOD"
        elif total_issues <= 2 and total_warnings <= 5:
            status = "⚠️ NEEDS ATTENTION"
        else:
            status = "❌ SECURITY RISKS"
        
        report = {
            'timestamp': '2024-09-09T12:00:00Z',  # In real implementation, use datetime.utcnow()
            'status': status,
            'summary': {
                'total_issues': total_issues,
                'total_warnings': total_warnings,
                'total_info': len(self.info)
            },
            'issues': self.issues,
            'warnings': self.warnings,
            'info': self.info,
            'recommendations': self._get_recommendations()
        }
        
        return report
    
    def _get_recommendations(self) -> List[str]:
        """Get security recommendations based on findings."""
        recommendations = []
        
        if any('password' in issue['message'].lower() for issue in self.issues):
            recommendations.append("Remove all hardcoded passwords and use environment variables")
        
        if any('api_key' in issue['message'].lower() for issue in self.issues):
            recommendations.append("Move API keys to environment variables or .env file")
        
        if any('http://' in issue['message'] for issue in self.warnings):
            recommendations.append("Replace HTTP URLs with HTTPS for production")
        
        if any('ssl' in issue['message'].lower() for issue in self.issues):
            recommendations.append("Enable SSL certificate verification")
        
        if any('logging' in issue['message'].lower() for issue in self.warnings):
            recommendations.append("Review logging practices to avoid sensitive data exposure")
        
        if len(self.warnings) > 5:
            recommendations.append("Address security warnings before production deployment")
        
        # Default recommendations
        if not recommendations:
            recommendations.extend([
                "Regularly update dependencies to latest secure versions",
                "Implement proper error handling to avoid information leakage",
                "Use environment variables for all configuration secrets",
                "Enable log encryption for production deployments"
            ])
        
        return recommendations


def main():
    """Main entry point for security checker."""
    parser = argparse.ArgumentParser(description='Fusion 360 Co-Pilot Security Checker')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output', '-o', help='Output report to file (JSON)')
    parser.add_argument('--project-root', default='..', help='Project root directory')
    
    args = parser.parse_args()
    
    # Determine project root
    if args.project_root == '..':
        project_root = Path(__file__).parent.parent
    else:
        project_root = Path(args.project_root)
    
    print(f"🔒 Fusion 360 Co-Pilot Security Check")
    print(f"📁 Project: {project_root.absolute()}")
    print(f"=" * 60)
    
    # Run security checks
    checker = SecurityChecker(str(project_root), args.verbose)
    
    checker.check_hardcoded_secrets()
    checker.check_network_security()
    checker.check_input_validation()
    checker.check_logging_security()
    checker.check_environment_config()
    checker.check_file_permissions()
    checker.check_dependencies()
    
    # Generate report
    report = checker.generate_report()
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🎯 SECURITY REPORT")
    print(f"Status: {report['status']}")
    print(f"Issues: {report['summary']['total_issues']}")
    print(f"Warnings: {report['summary']['total_warnings']}")
    print(f"Info: {report['summary']['total_info']}")
    
    # Print issues and warnings
    if report['issues']:
        print(f"\n❌ ISSUES ({len(report['issues'])}):")
        for issue in report['issues']:
            file_info = f" [{issue['file']}]" if issue['file'] else ""
            print(f"  • {issue['message']}{file_info}")
    
    if report['warnings']:
        print(f"\n⚠️ WARNINGS ({len(report['warnings'])}):")
        for warning in report['warnings'][:10]:  # Limit output
            file_info = f" [{warning['file']}]" if warning['file'] else ""
            print(f"  • {warning['message']}{file_info}")
        
        if len(report['warnings']) > 10:
            print(f"  ... and {len(report['warnings']) - 10} more warnings")
    
    # Print recommendations
    if report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to: {args.output}")
    
    # Exit with appropriate code
    if report['summary']['total_issues'] > 0:
        print(f"\n❌ Security issues found. Address before production deployment.")
        sys.exit(1)
    elif report['summary']['total_warnings'] > 3:
        print(f"\n⚠️ Multiple security warnings. Review recommended.")
        sys.exit(2)
    else:
        print(f"\n✅ Security check passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()