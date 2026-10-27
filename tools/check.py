"""check.py: the repo's one-command check (unit tests). The pre-commit hook runs this; exit code gates the commit."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    sys.exit(subprocess.run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-t', '.', '-q'],
                            cwd=ROOT).returncode)
