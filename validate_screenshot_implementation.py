#!/usr/bin/env python3
"""
Validation script for screenshot implementation
Tests the implementation without requiring external dependencies
"""

import sys
import ast
import json
from pathlib import Path
from typing import Dict, List, Any

class ImplementationValidator:
    """Validates the screenshot implementation"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.results = []
        self.errors = []
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message
        }
        self.results.append(result)
        
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {message}")
        
        if not success:
            self.errors.append(test_name)
    
    def validate_file_structure(self) -> bool:
        """Validate file structure"""
        print("\n🔍 Validating file structure...")
        
        required_files = [
            # Core interfaces
            "python/helpers/screenshots/__init__.py",
            "python/helpers/screenshots/interfaces/__init__.py",
            "python/helpers/screenshots/interfaces/screenshot_provider.py",
            
            # Providers
            "python/helpers/screenshots/providers/__init__.py",
            "python/helpers/screenshots/providers/playwright_provider.py",
            
            # Managers
            "python/helpers/screenshots/managers/__init__.py",
            "python/helpers/screenshots/managers/browser_screenshot_manager.py",
            "python/helpers/screenshots/managers/auto_screenshot_manager.py",
            
            # Utilities
            "python/helpers/screenshots/utils/__init__.py",
            "python/helpers/screenshots/utils/path_utils.py",
            "python/helpers/screenshots/utils/cleanup_utils.py",
            "python/helpers/screenshots/utils/validation_utils.py",
            
            # Storage
            "python/helpers/screenshots/storage/__init__.py",
            "python/helpers/screenshots/storage/file_storage.py",
            
            # Tools
            "python/tools/screenshot_tool.py",
            "python/tools/browser_agent_enhanced.py",
            
            # Settings
            "python/helpers/settings_screenshot_integration.py",
            
            # Prompts
            "prompts/default/agent.system.tool.screenshot.md",
            
            # Documentation
            "docs/screenshots.md",
            
            # Tests
            "tests/screenshots/test_screenshot_provider.py",
            "tests/screenshots/test_screenshot_manager.py",
            
            # Deployment
            "deploy_screenshot_system.py",
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                self.log_result(f"File exists: {file_path}", True)
            else:
                self.log_result(f"File missing: {file_path}", False)
                all_exist = False
        
        return all_exist
    
    def validate_python_syntax(self) -> bool:
        """Validate Python syntax"""
        print("\n🔍 Validating Python syntax...")
        
        python_files = [
            "python/helpers/screenshots/__init__.py",
            "python/helpers/screenshots/interfaces/screenshot_provider.py",
            "python/helpers/screenshots/providers/playwright_provider.py",
            "python/helpers/screenshots/managers/browser_screenshot_manager.py",
            "python/helpers/screenshots/managers/auto_screenshot_manager.py",
            "python/helpers/screenshots/utils/path_utils.py",
            "python/helpers/screenshots/utils/cleanup_utils.py",
            "python/helpers/screenshots/utils/validation_utils.py",
            "python/helpers/screenshots/storage/file_storage.py",
            "python/tools/screenshot_tool.py",
            "python/tools/browser_agent_enhanced.py",
            "python/helpers/settings_screenshot_integration.py",
            "deploy_screenshot_system.py",
        ]
        
        all_valid = True
        for file_path in python_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse AST to check syntax
                    ast.parse(content)
                    self.log_result(f"Syntax valid: {file_path}", True)
                    
                except SyntaxError as e:
                    self.log_result(f"Syntax error in {file_path}", False, f"Line {e.lineno}: {e.msg}")
                    all_valid = False
                except Exception as e:
                    self.log_result(f"Parse error in {file_path}", False, str(e))
                    all_valid = False
            else:
                self.log_result(f"File not found: {file_path}", False)
                all_valid = False
        
        return all_valid
    
    def validate_class_structure(self) -> bool:
        """Validate class structure and interfaces"""
        print("\n🔍 Validating class structure...")
        
        # Check interface file
        interface_file = self.base_path / "python/helpers/screenshots/interfaces/screenshot_provider.py"
        if not interface_file.exists():
            self.log_result("Interface file missing", False)
            return False
        
        try:
            with open(interface_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for required classes
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            required_classes = ['ScreenshotConfig', 'ScreenshotResult', 'ScreenshotProvider']
            for class_name in required_classes:
                if class_name in classes:
                    self.log_result(f"Class found: {class_name}", True)
                else:
                    self.log_result(f"Class missing: {class_name}", False)
                    return False
            
            # Check for required methods in ScreenshotProvider
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == 'ScreenshotProvider':
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    required_methods = ['capture_screenshot', 'is_available', 'cleanup', 'get_capabilities']
                    
                    for method_name in required_methods:
                        if method_name in methods:
                            self.log_result(f"Method found: {method_name}", True)
                        else:
                            self.log_result(f"Method missing: {method_name}", False)
                            return False
            
            return True
            
        except Exception as e:
            self.log_result("Class structure validation failed", False, str(e))
            return False
    
    def validate_imports(self) -> bool:
        """Validate import statements"""
        print("\n🔍 Validating import statements...")
        
        # Check main module __init__.py
        init_file = self.base_path / "python/helpers/screenshots/__init__.py"
        if not init_file.exists():
            self.log_result("Main __init__.py missing", False)
            return False
        
        try:
            with open(init_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for expected imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append(alias.name)
            
            expected_imports = ['ScreenshotProvider', 'ScreenshotConfig', 'ScreenshotResult', 'PlaywrightScreenshotProvider', 'BrowserScreenshotManager']
            
            for imp in expected_imports:
                if imp in imports:
                    self.log_result(f"Import found: {imp}", True)
                else:
                    self.log_result(f"Import missing: {imp}", False)
                    return False
            
            return True
            
        except Exception as e:
            self.log_result("Import validation failed", False, str(e))
            return False
    
    def validate_documentation(self) -> bool:
        """Validate documentation files"""
        print("\n🔍 Validating documentation...")
        
        doc_files = [
            ("docs/screenshots.md", "Main documentation"),
            ("prompts/default/agent.system.tool.screenshot.md", "Tool prompt"),
            ("SCREENSHOTS-ENHANCED.md", "Enhanced implementation report"),
        ]
        
        all_valid = True
        for file_path, description in doc_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Basic content validation
                    if len(content) > 100:  # Minimum content length
                        self.log_result(f"Documentation valid: {description}", True)
                    else:
                        self.log_result(f"Documentation too short: {description}", False)
                        all_valid = False
                        
                except Exception as e:
                    self.log_result(f"Documentation error: {description}", False, str(e))
                    all_valid = False
            else:
                self.log_result(f"Documentation missing: {description}", False)
                all_valid = False
        
        return all_valid
    
    def validate_test_files(self) -> bool:
        """Validate test files"""
        print("\n🔍 Validating test files...")
        
        test_files = [
            "tests/screenshots/test_screenshot_provider.py",
            "tests/screenshots/test_screenshot_manager.py",
        ]
        
        all_valid = True
        for file_path in test_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # Check for test functions
                    tree = ast.parse(content)
                    test_functions = [
                        node.name for node in ast.walk(tree) 
                        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
                    ]
                    
                    if len(test_functions) > 0:
                        self.log_result(f"Test file valid: {file_path} ({len(test_functions)} tests)", True)
                    else:
                        self.log_result(f"No test functions found: {file_path}", False)
                        all_valid = False
                        
                except Exception as e:
                    self.log_result(f"Test file error: {file_path}", False, str(e))
                    all_valid = False
            else:
                self.log_result(f"Test file missing: {file_path}", False)
                all_valid = False
        
        return all_valid
    
    def validate_integration_points(self) -> bool:
        """Validate integration points"""
        print("\n🔍 Validating integration points...")
        
        # Check enhanced browser agent
        browser_agent_file = self.base_path / "python/tools/browser_agent_enhanced.py"
        if browser_agent_file.exists():
            try:
                with open(browser_agent_file, 'r') as f:
                    content = f.read()
                
                # Check for screenshot integration
                if "screenshot_manager" in content and "auto_screenshot_manager" in content:
                    self.log_result("Browser agent integration", True)
                else:
                    self.log_result("Browser agent integration incomplete", False)
                    return False
                    
            except Exception as e:
                self.log_result("Browser agent validation failed", False, str(e))
                return False
        else:
            self.log_result("Enhanced browser agent missing", False)
            return False
        
        # Check settings integration
        settings_file = self.base_path / "python/helpers/settings_screenshot_integration.py"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    content = f.read()
                
                # Check for settings functions
                if "get_screenshot_settings_fields" in content:
                    self.log_result("Settings integration", True)
                else:
                    self.log_result("Settings integration incomplete", False)
                    return False
                    
            except Exception as e:
                self.log_result("Settings integration validation failed", False, str(e))
                return False
        else:
            self.log_result("Settings integration missing", False)
            return False
        
        return True
    
    def run_validation(self) -> bool:
        """Run complete validation"""
        print("🚀 Screenshot Implementation Validation")
        print("=" * 50)
        
        validation_steps = [
            ("File Structure", self.validate_file_structure),
            ("Python Syntax", self.validate_python_syntax),
            ("Class Structure", self.validate_class_structure),
            ("Import Statements", self.validate_imports),
            ("Documentation", self.validate_documentation),
            ("Test Files", self.validate_test_files),
            ("Integration Points", self.validate_integration_points),
        ]
        
        all_passed = True
        for step_name, step_func in validation_steps:
            try:
                if not step_func():
                    all_passed = False
            except Exception as e:
                self.log_result(f"{step_name} validation failed", False, str(e))
                all_passed = False
        
        print("\n" + "=" * 50)
        if all_passed:
            print("✅ All validation tests passed!")
            print("🎉 Screenshot implementation is ready for deployment")
        else:
            print("❌ Validation failed!")
            print(f"💥 {len(self.errors)} errors found:")
            for error in self.errors:
                print(f"  - {error}")
        
        return all_passed
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        return {
            "validation_passed": len(self.errors) == 0,
            "total_tests": len(self.results),
            "passed_tests": len([r for r in self.results if r["success"]]),
            "failed_tests": len([r for r in self.results if not r["success"]]),
            "errors": self.errors,
            "results": self.results
        }

def main():
    """Main validation function"""
    base_path = Path(__file__).parent
    
    validator = ImplementationValidator(base_path)
    success = validator.run_validation()
    
    # Save report
    report = validator.generate_report()
    report_file = base_path / "validation_report.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Validation report saved to: {report_file}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())