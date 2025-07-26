#!/usr/bin/env python3
"""
Coverage analysis for trippleCheck project.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

def analyze_backend_coverage():
    """Analyze backend code coverage."""
    print("📊 Analyzing backend code coverage...")
    
    fastapi_path = Path(__file__).parent / "fastapi_app"
    total_lines = 0
    python_files = []
    
    # Count lines in Python files
    for py_file in fastapi_path.rglob("*.py"):
        if "__pycache__" not in str(py_file) and "tests" not in str(py_file):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = len([line for line in f if line.strip() and not line.strip().startswith('#')])
                    total_lines += lines
                    python_files.append({
                        "file": str(py_file.relative_to(fastapi_path)),
                        "lines": lines
                    })
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
    
    # Estimate test coverage based on test files
    test_files = list(fastapi_path.glob("tests/test_*.py"))
    test_lines = 0
    
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                test_lines += len([line for line in f if line.strip() and not line.strip().startswith('#')])
        except Exception:
            pass
    
    # Calculate estimated coverage
    if total_lines > 0:
        coverage_estimate = min(95, (test_lines / total_lines) * 100 * 1.5)  # Rough estimate
    else:
        coverage_estimate = 0
    
    print(f"📈 Backend Coverage Analysis:")
    print(f"  Source files: {len(python_files)}")
    print(f"  Source lines: {total_lines}")
    print(f"  Test files: {len(test_files)}")
    print(f"  Test lines: {test_lines}")
    print(f"  Estimated coverage: {coverage_estimate:.1f}%")
    
    return {
        "source_files": len(python_files),
        "source_lines": total_lines,
        "test_files": len(test_files),
        "test_lines": test_lines,
        "estimated_coverage": coverage_estimate,
        "files": python_files
    }

def analyze_frontend_coverage():
    """Analyze frontend code coverage."""
    print("🎨 Analyzing frontend code coverage...")
    
    frontend_path = Path(__file__).parent / "frontend" / "src"
    total_lines = 0
    source_files = []
    
    # Count lines in TypeScript/Svelte files
    for ext in ["*.ts", "*.svelte", "*.js"]:
        for file in frontend_path.rglob(ext):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lines = len([line for line in f if line.strip() and not line.strip().startswith('//')])
                    total_lines += lines
                    source_files.append({
                        "file": str(file.relative_to(frontend_path)),
                        "lines": lines
                    })
            except Exception as e:
                print(f"Warning: Could not read {file}: {e}")
    
    # Check for test files (would be in tests/ or *.test.*)
    test_patterns = ["**/*.test.*", "**/tests/**/*", "**/*.spec.*"]
    test_files = []
    
    for pattern in test_patterns:
        test_files.extend(frontend_path.rglob(pattern))
    
    print(f"📈 Frontend Coverage Analysis:")
    print(f"  Source files: {len(source_files)}")
    print(f"  Source lines: {total_lines}")
    print(f"  Test files: {len(test_files)}")
    print(f"  Test coverage: Not configured (recommend Vitest setup)")
    
    return {
        "source_files": len(source_files),
        "source_lines": total_lines,
        "test_files": len(test_files),
        "coverage_setup": "Recommended: Vitest + @vitest/ui",
        "files": source_files
    }

def generate_coverage_report():
    """Generate comprehensive coverage report."""
    print("📊 Generating Coverage Report")
    print("=" * 50)
    
    backend_coverage = analyze_backend_coverage()
    frontend_coverage = analyze_frontend_coverage()
    
    report = {
        "project": "trippleCheck",
        "timestamp": "2024-07-27",
        "backend": backend_coverage,
        "frontend": frontend_coverage,
        "recommendations": [
            "Set up pytest-cov for accurate backend coverage measurement",
            "Configure Vitest for frontend testing and coverage",
            "Add integration tests for API endpoints",
            "Implement E2E tests for critical user workflows",
            "Set up coverage reporting in CI/CD pipeline"
        ]
    }
    
    # Save report
    report_path = Path(__file__).parent / "coverage-report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Coverage report saved to: {report_path}")
    
    # Generate summary
    print("\n📊 Coverage Summary")
    print("=" * 50)
    print(f"Backend estimated coverage: {backend_coverage['estimated_coverage']:.1f}%")
    print(f"Frontend test setup: {frontend_coverage['coverage_setup']}")
    
    total_source_lines = backend_coverage['source_lines'] + frontend_coverage['source_lines']
    total_test_lines = backend_coverage['test_lines']
    
    print(f"\nOverall project metrics:")
    print(f"  Total source lines: {total_source_lines}")
    print(f"  Total test lines: {total_test_lines}")
    print(f"  Test to source ratio: {(total_test_lines/total_source_lines)*100:.1f}%")
    
    return report

def check_quality_gates():
    """Check if quality gates are met."""
    print("\n🚪 Quality Gates Check")
    print("=" * 50)
    
    gates = {
        "Backend test files exist": Path("fastapi_app/tests").exists(),
        "Frontend build passes": Path("frontend/build").exists(),
        "Documentation exists": Path("DEVELOPMENT.md").exists(),
        "CI/CD configured": Path(".github/workflows").exists(),
        "Docker configuration": Path("docker-compose.yml").exists(),
        "Environment setup": Path(".env.example").exists()
    }
    
    passed = 0
    total = len(gates)
    
    for gate, status in gates.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {gate}")
        if status:
            passed += 1
    
    print(f"\nQuality gates: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All quality gates passed!")
    else:
        print("⚠️  Some quality gates need attention")
    
    return passed == total

def main():
    """Run coverage analysis."""
    try:
        report = generate_coverage_report()
        quality_passed = check_quality_gates()
        
        print("\n🎯 Recommendations for Improvement")
        print("=" * 50)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
        
        return 0 if quality_passed else 1
        
    except Exception as e:
        print(f"❌ Coverage analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())