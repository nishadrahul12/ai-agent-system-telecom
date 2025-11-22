"""
Infrastructure Verification Script for Phase 1.3

Validates all infrastructure components before proceeding with handlers.

Run: python verify_infrastructure.py

Checks:
    1. All directories exist
    2. All required files present
    3. All imports working
    4. Configuration loaded
    5. Models validated
    6. Utilities functional
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_directories() -> bool:
    """Verify all required directories exist."""
    required_dirs = [
        "Phase1",
        "Phase1/api",
        "Phase1/api/tests",
        "Phase1/utils",
        "data",
        "logs",
    ]
    
    print("\n📁 Checking directories...")
    all_exist = True
    for directory in required_dirs:
        path = PROJECT_ROOT / directory
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {directory}/")
        if not exists:
            all_exist = False
    
    return all_exist


def check_files() -> bool:
    """Verify all required files exist."""
    required_files = [
        "Phase1/config.py",
        "Phase1/api/__init__.py",
        "Phase1/api/models.py",
        "Phase1/utils/__init__.py",
        "Phase1/utils/logging_config.py",
        "Phase1/utils/errors.py",
        "Phase1/utils/tests.py",
    ]
    
    print("\n📄 Checking files...")
    all_exist = True
    for filepath in required_files:
        path = PROJECT_ROOT / filepath
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {filepath}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_imports() -> bool:
    """Verify all imports work."""
    print("\n🔗 Checking imports...")
    
    imports_to_test = [
        ("Phase1.config", "Config"),
        ("Phase1.utils", "setup_logging"),
        ("Phase1.utils", "FileValidationError"),
        ("Phase1.api", "AnalysisRequest"),
        ("Phase1.api.models", "AnalysisResultResponse"),
    ]
    
    all_ok = True
    for module, item in imports_to_test:
        try:
            exec(f"from {module} import {item}")
            print(f"  ✓ from {module} import {item}")
        except ImportError as e:
            print(f"  ✗ from {module} import {item} - {e}")
            all_ok = False
    
    return all_ok


def check_config() -> bool:
    """Verify configuration loads correctly."""
    print("\n⚙️  Checking configuration...")
    
    try:
        from Phase1.config import Config
        
        checks = [
            ("PROJECT_ROOT", Config.PROJECT_ROOT),
            ("DEBUG", Config.DEBUG),
            ("UPLOAD_DIR", Config.UPLOAD_DIR),
            ("MAX_FILE_SIZE_BYTES", Config.MAX_FILE_SIZE_BYTES),
            ("ALLOWED_EXTENSIONS", Config.ALLOWED_EXTENSIONS),
        ]
        
        all_ok = True
        for name, value in checks:
            if value is not None:
                print(f"  ✓ {name}: {value}")
            else:
                print(f"  ✗ {name}: None")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"  ✗ Configuration check failed: {e}")
        return False


def check_models() -> bool:
    """Verify Pydantic models validate correctly."""
    print("\n📊 Checking models...")
    
    try:
        from Phase1.api.models import (
            AnalysisRequest,
            AnalysisStatusResponse,
            AnalysisResultResponse,
            ErrorResponse,
        )
        from datetime import datetime
        
        # Test AnalysisRequest
        req = AnalysisRequest(
            file_id="test_file_123",
            target_variable="drop_rate",
            correlation_method="pearson"
        )
        print(f"  ✓ AnalysisRequest: {req.file_id}")
        
        # Test ErrorResponse
        err = ErrorResponse(
            error="TEST_ERROR",
            message="Test error message",
            details={"test": "value"}
        )
        print(f"  ✓ ErrorResponse: {err.error}")
        
        return True
    except Exception as e:
        print(f"  ✗ Model validation failed: {e}")
        return False


def check_utilities() -> bool:
    """Verify utilities work correctly."""
    print("\n🛠️  Checking utilities...")
    
    try:
        from Phase1.utils import setup_logging, FileValidationError
        
        # Test logger creation
        logger = setup_logging("verify_test")
        print(f"  ✓ Logger created: {logger.name}")
        
        # Test error creation
        error = FileValidationError("Test error", "test.txt")
        error_dict = error.to_dict()
        print(f"  ✓ FileValidationError: {error_dict['error']}")
        
        return True
    except Exception as e:
        print(f"  ✗ Utilities check failed: {e}")
        return False


def main() -> int:
    """Run all verification checks."""
    print("=" * 60)
    print("🚀 PHASE 1.3 INFRASTRUCTURE VERIFICATION")
    print("=" * 60)
    
    results = {
        "Directories": check_directories(),
        "Files": check_files(),
        "Imports": check_imports(),
        "Configuration": check_config(),
        "Models": check_models(),
        "Utilities": check_utilities(),
    }
    
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {check_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Infrastructure is ready!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review errors above")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
