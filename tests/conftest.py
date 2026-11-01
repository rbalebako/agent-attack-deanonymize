import os
import sys
from pathlib import Path

# Make top-level modules (models, cost_tracker, main) importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Importing main builds the ADK agents, and get_model() requires a key to be
# set. A dummy value is enough: no model calls are made in these tests.
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
