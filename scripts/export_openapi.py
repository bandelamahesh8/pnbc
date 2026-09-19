import json
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.main import app

openapi_schema = app.openapi()
out_path = root_dir / "openapi.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2)

print(f"Exported OpenAPI schema to {out_path}")
