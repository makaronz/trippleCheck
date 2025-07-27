#!/usr/bin/env python3
"""
Check requirements files for common issues.
"""

import sys
from pathlib import Path

def check_requirements_file(file_path: Path) -> bool:
    """Check a requirements file for common issues."""
    if not file_path.exists():
        print(f"❌ Requirements file not found: {file_path}")
        return False
    
    print(f"📋 Checking {file_path}...")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    issues = []
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Check for common issues
        if '==' in line and '>=' in line:
            issues.append(f"Line {i}: Mixed version specifiers: {line}")
        
        if line.startswith('-'):
            if not line.startswith('-r ') and not line.startswith('--'):
                issues.append(f"Line {i}: Suspicious line starting with dash: {line}")
    
    if issues:
        print("⚠️ Issues found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ No issues found")
        return True

def main():
    """Main function."""
    print("🔍 Checking requirements files...")
    print("=" * 50)
    
    repo_root = Path(__file__).parent.parent
    requirements_files = [
        repo_root / "fastapi_app" / "requirements.txt",
        repo_root / "fastapi_app" / "requirements_dev.txt",
    ]
    
    all_good = True
    for req_file in requirements_files:
        if req_file.exists():
            if not check_requirements_file(req_file):
                all_good = False
        else:
            print(f"ℹ️ Optional file not found: {req_file}")
    
    print("=" * 50)
    if all_good:
        print("✅ All requirements files are valid!")
        return 0
    else:
        print("❌ Issues found in requirements files")
        return 1

if __name__ == "__main__":
    sys.exit(main())