import sys
from pathlib import Path

# Guarantees the backend/ directory itself is importable as the root of
# the "app" package, regardless of which directory pytest is invoked
# from (project root, backend/, etc).
sys.path.insert(0, str(Path(__file__).resolve().parent))
