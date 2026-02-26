#!/usr/bin/env python3
"""
INSTALL_APPS Dependency Detector - Python 3.12+ Compatible
No pkg_resources needed!
"""

import sys
import importlib.metadata as imeta

print("=" * 60)
print("INSTALL_APPS DEPENDENCY ANALYSIS (Python 3.12+)")
print("=" * 60)
print(f"Python Version: {sys.version}")
print(f"Version Info:   {sys.version_info}")
print()

# Get ALL installed packages (Python 3.12 way)
packages = [(dist.metadata["Name"], dist.version) for dist in imeta.distributions()]
packages = sorted(packages, key=lambda x: x[0].lower())

# Filter out common system packages
common_system = {'pip', 'setuptools', 'wheel'}
project_deps = [pkg for pkg in packages if pkg[0].lower() not in common_system]

print(f"📦 Total packages: {len(packages)}")
print(f"🏆 Project deps:   {len(project_deps)}")
print()

print("TOP 20 DEPENDENCIES:")
for name, version in project_deps[:20]:
    print(f"  {name:<25} v{version}")

# Generate requirements.txt
with open('requirements.txt', 'w') as f:
    f.write(f"# INSTALL_APPS Requirements - Python {sys.version_info.major}.{sys.version_info.minor}\n")
    f.write(f"# Generated: {sys.version}\n\n")
    for name, version in project_deps:
        f.write(f'{name}=={version}\n')

print(f"\n✅ Saved {len(project_deps)} packages to requirements.txt")

print("\n🚀 TO RECREATE ENVIRONMENT:")
print("pip install -r requirements.txt")
