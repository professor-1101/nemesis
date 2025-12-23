# -*- coding: utf-8 -*-
"""Script to run nemesis tests with proper encoding."""
import os
import sys
import subprocess

# Set encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Fix stdout/stderr encoding
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Run nemesis with tag to only run authentication feature
cmd = ["nemesis", "run", "--report", "all", "--tags", "@authentication"]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, encoding='utf-8', errors='replace')
sys.exit(result.returncode)

