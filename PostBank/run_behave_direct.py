# -*- coding: utf-8 -*-
"""Run behave directly to test encoding."""
import sys
import os
import subprocess

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Fix stdout/stderr for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Run behave
feature_file = "features/vorood_karbar_enteghal_be_dashboard/vorood_karbar_enteghal_be_dashboard.feature"
cmd = ["behave", feature_file, "--tags", "@file_data", "--stop", "--no-capture"]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, encoding='utf-8', errors='replace')
sys.exit(result.returncode)


