"""Single-command local startup: python start.py"""
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parent
for args in (["manage.py", "migrate", "--noinput"], ["manage.py", "ingest_events"], ["manage.py", "reconcile_events"], ["manage.py", "runserver"]):
    subprocess.run([sys.executable, *args], cwd=root, check=True)
