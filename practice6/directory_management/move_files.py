from pathlib import Path
import shutil
src_csv = base / "src" / "data.csv"
shutil.copy(src_csv, base / "data" / "raw" / "data.csv")
print("\n4. Copied data.csv → project/data/raw/")

src_txt = base / "src" / "notes.txt"
src_txt.rename(base / "data" / "processed" / "notes.txt")
print("   Moved notes.txt → project/data/processed/")

print("\n   project/data/raw:", [f.name for f in (base / "data" / "raw").iterdir()])
print("   project/data/processed:", [f.name for f in (base / "data" / "processed").iterdir()])