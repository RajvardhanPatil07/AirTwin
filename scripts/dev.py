"""Run the connected dashboard and API without rebuilding environmental data."""
from pathlib import Path
import os
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
processes = []

def healthy():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2) as response:
            return response.status == 200
    except OSError:
        return False

try:
    if not healthy():
        python = next((str(ROOT / name / 'bin/python') for name in ('.venv311', '.venv')
                       if (ROOT / name / 'bin/python').exists()), sys.executable)
        processes.append(subprocess.Popen([python, '-m', 'uvicorn', 'app.main:app', '--app-dir', 'backend',
                                            '--host', '127.0.0.1', '--port', '8000'], cwd=ROOT))
        deadline = time.monotonic() + 300
        while not healthy():
            if processes[0].poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('Backend did not become healthy. Check its startup output.')
            time.sleep(1)
    processes.append(subprocess.Popen(['npm', 'run', 'dev', '--', '--port', os.getenv('AIRTWIN_FRONTEND_PORT', '5188'),
                                      '--strictPort'], cwd=ROOT / 'frontend'))
    print('Connected dashboard: http://127.0.0.1:' + os.getenv('AIRTWIN_FRONTEND_PORT', '5188'), flush=True)
    processes[-1].wait()
except KeyboardInterrupt:
    pass
finally:
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
