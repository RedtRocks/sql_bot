#!/usr/bin/env python3
"""
Pre-deployment verification script
Checks if all necessary files and configurations are in place for Vercel deployment
"""

import os
import json
import sys

def check_file_exists(path, required=True):
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {path}: {'Found' if exists else 'Missing'}")
    return exists

def check_env_example():
    """Check if env.example has all required variables"""
    required_vars = [
        'POSTGRES_URL',
        'JWT_SECRET',
        'AZURE_OPENAI_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_DEPLOYMENT'
    ]
    
    if not os.path.exists('api/env.example'):
        print("⚠️ api/env.example not found")
        return False
    
    with open('api/env.example', 'r') as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if var not in content:
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables in env.example: {', '.join(missing)}")
        return False
    else:
        print("✅ All required environment variables documented")
        return True

def check_vercel_json():
    """Verify vercel.json configuration"""
    if not os.path.exists('vercel.json'):
        print("❌ vercel.json not found")
        return False
    
    with open('vercel.json', 'r') as f:
        config = json.load(f)
    
    # Check builds configuration
    if 'builds' not in config:
        print("❌ vercel.json missing 'builds' configuration")
        return False
    
    # Check routes configuration
    if 'routes' not in config:
        print("❌ vercel.json missing 'routes' configuration")
        return False
    
    print("✅ vercel.json properly configured")
    return True

def check_requirements():
    """Check if all required Python packages are listed"""
    if not os.path.exists('api/requirements.txt'):
        print("❌ api/requirements.txt not found")
        return False
    
    with open('api/requirements.txt', 'r') as f:
        content = f.read()
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'psycopg2-binary',
        'pyjwt',
        'passlib',
        'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        if package not in content.lower():
            missing.append(package)
    
    if missing:
        print(f"❌ Missing Python packages: {', '.join(missing)}")
        return False
    else:
        print("✅ All required Python packages listed")
        return True

def check_build_output():
    """Check if frontend build exists"""
    if not os.path.exists('dist'):
        print("❌ dist/ folder not found - run 'npm run build'")
        return False
    
    if not os.path.exists('dist/index.html'):
        print("❌ dist/index.html not found - build may have failed")
        return False
    
    print("✅ Frontend build output found")
    return True

def main():
    print("=" * 60)
    print("🚀 PRE-DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print()
    
    checks = []
    
    print("📁 Checking required files...")
    checks.append(check_file_exists('vercel.json', required=True))
    checks.append(check_file_exists('package.json', required=True))
    checks.append(check_file_exists('api/main.py', required=True))
    checks.append(check_file_exists('api/requirements.txt', required=True))
    checks.append(check_file_exists('.vercelignore', required=False))
    print()
    
    print("🔧 Checking configurations...")
    checks.append(check_vercel_json())
    checks.append(check_requirements())
    checks.append(check_env_example())
    print()
    
    print("🏗️ Checking build output...")
    checks.append(check_build_output())
    print()
    
    print("=" * 60)
    if all(checks):
        print("✅ ALL CHECKS PASSED - Ready for deployment!")
        print()
        print("📝 Next steps:")
        print("1. Set environment variables in Vercel dashboard")
        print("2. Push to GitHub: git push origin main")
        print("3. Deploy via Vercel dashboard or CLI")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before deploying")
        print()
        print("📝 Fix the issues above and run this script again")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
