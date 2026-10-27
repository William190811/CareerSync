"""Build the Vite frontend and stage the minimal Databricks Apps source tree."""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".databricks_app"

subprocess.run(["npm.cmd" if __import__("os").name == "nt" else "npm", "run", "build"],
               cwd=ROOT / "frontend", check=True)
if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(ROOT / "api", OUT / "api", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copytree(ROOT / "frontend" / "dist", OUT / "api" / "static")
shutil.copy2(ROOT / "app.yaml", OUT / "app.yaml")
shutil.copy2(ROOT / "requirements.txt", OUT / "requirements.txt")
assert (OUT / "api" / "static" / "index.html").is_file()
print(f"Databricks app source staged at {OUT}")
