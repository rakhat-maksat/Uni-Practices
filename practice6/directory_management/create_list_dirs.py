from pathlib import Path
import shutil

# Create nested directories
base = Path("project")
(base / "src" / "utils").mkdir(parents=True, exist_ok=True)
(base / "data" / "raw").mkdir(parents=True, exist_ok=True)
(base / "data" / "processed").mkdir(parents=True, exist_ok=True)
print("1. Nested directories created.")

# List files and folders
for name in ["main.py", "utils.py", "notes.txt", "data.csv"]:
    (base / "src" / name).touch()

print("\n2. Contents of project/src:")
for item in (base / "src").iterdir():
    item_type = "DIR" if item.is_dir() else "FILE"
    print(f"   [{item_type}] {item.name}")

# Find files by extension
print("\n3. Finding files by extension:")
py_files  = list(base.rglob("*.py"))
txt_files = list(base.rglob("*.txt"))
csv_files = list(base.rglob("*.csv"))

print(f"   .py  files: {[f.name for f in py_files]}")
print(f"   .txt files: {[f.name for f in txt_files]}")
print(f"   .csv files: {[f.name for f in csv_files]}")

# Cleanup
shutil.rmtree(base)
print("\nCleanup done.")