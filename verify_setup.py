import sys
from pathlib import Path

def check_python_version():
    """Check Python version >= 3.8."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. You have {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_packages():
    """Check required packages are installed."""
    required = [
        "pandas",
        "numpy",
        "sklearn",
        "joblib",
        "fastapi",
        "uvicorn",
        "pydantic",
        "shap",
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    return len(missing) == 0

def check_files():
    """Check critical files exist."""
    project_root = Path(__file__).parent
    
    files_to_check = {
        "Config": project_root / "src" / "utils" / "config.py",
        "API": project_root / "src" / "api" / "main.py",
        "Prediction Service": project_root / "src" / "services" / "prediction_service.py",
        "Analytics Service": project_root / "src" / "services" / "analytics_service.py",
        "Interpretation Service": project_root / "src" / "services" / "interpretation_service.py",
        ".env": project_root / ".env",
    }
    
    all_exist = True
    for name, path in files_to_check.items():
        if path.exists():
            print(f"✅ {name}: {path.relative_to(project_root)}")
        else:
            print(f"❌ {name} MISSING: {path.relative_to(project_root)}")
            all_exist = False
    
    return all_exist

def check_artifacts():
    """Check ML artifacts exist."""
    project_root = Path(__file__).parent
    
    artifacts = {
        "Model": project_root / "models" / "random_forest_model.pkl",
        "Preprocessor": project_root / "artifacts" / "encoders" / "preprocessor.pkl",
        "Metadata": project_root / "artifacts" / "metadata" / "preprocessing_metadata.pkl",
    }
    
    all_exist = True
    for name, path in artifacts.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"✅ {name}: {size_mb:.2f} MB")
        else:
            print(f"⚠️  {name} MISSING: {path.relative_to(project_root)}")
            all_exist = False
    
    if not all_exist:
        print("    Run: python main.py --mode full")
    
    return all_exist

def check_env():
    """Check .env file is properly configured."""
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ .env file MISSING")
        print("   Run: cp .env.example .env")
        return False
    
    print(f"✅ .env exists")
    
    # Check key variables
    with open(env_file) as f:
        content = f.read()
    
    required_vars = ["API_PORT", "LOG_LEVEL", "MODEL_PATH"]
    missing_vars = [var for var in required_vars if var not in content]
    
    if missing_vars:
        print(f"⚠️  Missing in .env: {', '.join(missing_vars)}")
        return False
    
    print(f"✅ .env contains required variables")
    return True

def main():
    """Run all checks."""
    print("=" * 60)
    print("Ecologistic Intelligence - Setup Verification")
    print("=" * 60)
    print()
    
    print("📦 Python Version:")
    py_ok = check_python_version()
    print()
    
    print("📦 Required Packages:")
    pkg_ok = check_packages()
    print()
    
    print("📁 Project Files:")
    files_ok = check_files()
    print()
    
    print("🤖 ML Artifacts:")
    artifacts_ok = check_artifacts()
    print()
    
    print("⚙️  Configuration:")
    env_ok = check_env()
    print()
    
    print("=" * 60)
    all_ok = py_ok and pkg_ok and files_ok and env_ok
    
    if all_ok:
        print("✅ ALL CHECKS PASSED - Ready to run!")
        print()
        print("To start the API:")
        print("  python run_api.py")
        print()
        print("In another terminal, test:")
        print("  curl http://localhost:8000/health")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        if not artifacts_ok:
            print("🔧 Missing ML artifacts? Train them:")
            print("   python main.py --mode full")
        if not env_ok:
            print("🔧 Missing .env? Create it:")
            print("   cp .env.example .env")
        if not pkg_ok:
            print("🔧 Missing packages? Install them:")
            print("   pip install -r requirements.txt -r requirements-api.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
