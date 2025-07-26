#!/usr/bin/env python3
"""
CI/CD Pipeline validation for trippleCheck project.
"""

import yaml
import json
from pathlib import Path

def validate_github_workflow():
    """Validate GitHub Actions workflow configuration."""
    print("🔄 Validating GitHub Actions CI/CD Pipeline")
    print("=" * 50)
    
    workflow_path = Path(".github/workflows/ci.yml")
    
    if not workflow_path.exists():
        print("❌ GitHub Actions workflow not found")
        return False
    
    try:
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Validate workflow structure
        validations = {
            "Has name": "name" in workflow,
            "Has triggers": "on" in workflow,
            "Has jobs": "jobs" in workflow,
            "Has environment variables": "env" in workflow,
        }
        
        jobs = workflow.get("jobs", {})
        job_validations = {
            "Backend test job": "backend-test" in jobs,
            "Frontend test job": "frontend-test" in jobs,
            "Security scan job": "security-scan" in jobs,
            "Integration test job": "integration-test" in jobs,
            "Deploy job": "deploy" in jobs,
        }
        
        print("📋 Workflow Configuration:")
        for check, status in validations.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {check}")
        
        print("\n📋 Job Configuration:")
        for check, status in job_validations.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {check}")
        
        # Check backend test job details
        if "backend-test" in jobs:
            backend_job = jobs["backend-test"]
            backend_checks = {
                "Has Python setup": any("setup-python" in str(step) for step in backend_job.get("steps", [])),
                "Has dependency caching": any("cache" in str(step) for step in backend_job.get("steps", [])),
                "Has test execution": any("pytest" in str(step) for step in backend_job.get("steps", [])),
                "Has coverage reporting": any("codecov" in str(step) for step in backend_job.get("steps", [])),
            }
            
            print("\n📋 Backend Test Job:")
            for check, status in backend_checks.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {check}")
        
        # Check frontend test job details
        if "frontend-test" in jobs:
            frontend_job = jobs["frontend-test"]
            frontend_checks = {
                "Has Node.js setup": any("setup-node" in str(step) for step in frontend_job.get("steps", [])),
                "Has npm install": any("npm ci" in str(step) for step in frontend_job.get("steps", [])),
                "Has build test": any("npm run build" in str(step) for step in frontend_job.get("steps", [])),
                "Has type checking": any("npm run check" in str(step) for step in frontend_job.get("steps", [])),
            }
            
            print("\n📋 Frontend Test Job:")
            for check, status in frontend_checks.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {check}")
        
        all_validations = list(validations.values()) + list(job_validations.values())
        success_rate = sum(all_validations) / len(all_validations) * 100
        
        print(f"\n📊 Overall Pipeline Health: {success_rate:.1f}%")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Error validating workflow: {e}")
        return False

def validate_docker_configuration():
    """Validate Docker configuration."""
    print("\n🐳 Validating Docker Configuration")
    print("=" * 50)
    
    docker_files = {
        "Docker Compose": "docker-compose.yml",
        "Backend Dockerfile": "docker/Dockerfile.backend",
        "Frontend Dockerfile": "docker/Dockerfile.frontend",
        "Nginx config": "docker/nginx.conf"
    }
    
    validations = {}
    for name, file_path in docker_files.items():
        exists = Path(file_path).exists()
        validations[name] = exists
        status_icon = "✅" if exists else "❌"
        print(f"  {status_icon} {name}: {file_path}")
    
    # Check docker-compose.yml content
    if Path("docker-compose.yml").exists():
        try:
            with open("docker-compose.yml", 'r') as f:
                compose = yaml.safe_load(f)
            
            services = compose.get("services", {})
            service_checks = {
                "Backend service": "backend" in services,
                "Frontend service": "frontend" in services,
                "Health checks": any("healthcheck" in service for service in services.values()),
                "Environment variables": any("environment" in service for service in services.values()),
            }
            
            print("\n📋 Docker Compose Services:")
            for check, status in service_checks.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {check}")
                validations[check] = status
                
        except Exception as e:
            print(f"  ⚠️  Could not parse docker-compose.yml: {e}")
    
    success_rate = sum(validations.values()) / len(validations) * 100
    print(f"\n📊 Docker Configuration Health: {success_rate:.1f}%")
    
    return success_rate >= 80

def validate_testing_configuration():
    """Validate testing configuration."""
    print("\n🧪 Validating Testing Configuration")
    print("=" * 50)
    
    test_configs = {
        "pytest.ini": Path("pytest.ini").exists(),
        "pyproject.toml": Path("pyproject.toml").exists(),
        "Backend tests": Path("fastapi_app/tests").exists(),
        "Test fixtures": Path("fastapi_app/tests/conftest.py").exists(),
        "API tests": Path("fastapi_app/tests/test_api_endpoints.py").exists(),
        "Pipeline tests": Path("fastapi_app/tests/test_pipeline_service.py").exists(),
        "Custom test runner": Path("test-runner.py").exists(),
        "Coverage runner": Path("coverage-runner.py").exists(),
    }
    
    for name, exists in test_configs.items():
        status_icon = "✅" if exists else "❌"
        print(f"  {status_icon} {name}")
    
    success_rate = sum(test_configs.values()) / len(test_configs) * 100
    print(f"\n📊 Testing Configuration Health: {success_rate:.1f}%")
    
    return success_rate >= 80

def main():
    """Run CI/CD validation."""
    print("🔄 CI/CD Pipeline Validation")
    print("=" * 50)
    
    results = {
        "GitHub Actions": validate_github_workflow(),
        "Docker Configuration": validate_docker_configuration(),
        "Testing Configuration": validate_testing_configuration()
    }
    
    print("\n📊 Validation Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}")
        if status:
            passed += 1
    
    print(f"\nOverall CI/CD Health: {passed}/{total} components validated")
    
    if passed == total:
        print("🎉 CI/CD pipeline is ready for production!")
        return 0
    else:
        print("⚠️  Some CI/CD components need attention")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())