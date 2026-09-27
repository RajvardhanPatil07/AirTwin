"""Reject accidentally tracked secrets, generated outputs, and oversized files."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
errors = []
for name in filter(None, paths):
    path = Path(name)
    parts = path.parts
    if any(part in {'node_modules', 'dist', '__pycache__'} for part in parts):
        errors.append(f'Generated directory: {name}')
    if path.name.startswith('.env') and path.name != '.env.example':
        errors.append(f'Environment file: {name}')
    if path.suffix in {'.parquet', '.pkl', '.joblib', '.zip', '.mp4', '.mov'}:
        errors.append(f'Generated/binary data: {name}')
    if any(name.startswith(prefix) for prefix in ['data/raw/', 'data/processed/', 'backend/models/']) and path.name != '.gitkeep':
        errors.append(f'Generated data/model: {name}')
    size = (ROOT / path).stat().st_size
    limit = 1_000_000 if name.startswith('data/sample/') else 2_000_000
    if size >= limit:
        errors.append(f'Oversized file ({size} bytes): {name}')
if errors:
    raise SystemExit('\n'.join(errors))
print('Tracked-file hygiene passed. This check is not a credential-content scanner.')
