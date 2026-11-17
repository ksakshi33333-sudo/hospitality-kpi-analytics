"""One command to rebuild everything:  python run_all.py"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [("1/3  Generate sample data (pandas)", "src/generate_data.py"),
         ("2/3  Build SQLite DB + SQL aggregate tables", "src/build_db.py"),
         ("3/3  Write inference document", "src/generate_inference.py")]

for title, script in STEPS:
    print(f"\n=== {title} ===")
    t0 = time.time()
    subprocess.run([sys.executable, str(ROOT / script)], check=True)
    print(f"--- finished in {time.time() - t0:.0f}s")

print("\nAll done.  Start the dashboard with:\n    streamlit run dashboard/app.py")
