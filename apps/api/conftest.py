import sys
from pathlib import Path

# Make sure `apps/api` is on sys.path regardless of where pytest is invoked from, so both
# `import app...` and `import scripts.ingest` resolve the same way they do at runtime.
sys.path.insert(0, str(Path(__file__).resolve().parent))
