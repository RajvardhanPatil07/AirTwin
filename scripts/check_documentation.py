"""Reject broken local file links in tracked Markdown documents."""
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(['git', 'ls-files', '-z', '*.md'], cwd=ROOT).decode().split('\0')
errors, checked = [], 0
for name in filter(None, paths):
    path = ROOT / name
    text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
    for match in re.finditer(r'\]\(([^\n)]+)\)', text):
        target = match.group(1).split(' "', 1)[0].strip('<>')
        url = urlsplit(target)
        if url.scheme or target.startswith(('#', '//')):
            continue
        checked += 1
        resolved = (path.parent / unquote(url.path)).resolve()
        if not resolved.exists():
            errors.append(f'{name}: missing local link {target}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Local documentation links passed ({checked} targets). Remote access and heading anchors are not checked.')
