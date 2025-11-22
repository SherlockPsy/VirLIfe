#!/usr/bin/env python3
"""
Run all tests against production and generate summary report.
"""

import subprocess
import sys
import os

os.environ["PRODUCTION_DATABASE_URL"] = "postgresql://postgres:rUaCGawjVEoluMBJZzZgAerZfKPmTbQu@interchange.proxy.rlwy.net:50418/railway"

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)

sys.exit(result.returncode)

