import shutil
import os
shutil.copy("sample_data.txt", "file.txt")

for filename in ["sample_data.txt", "file.txt"]:
    if os.path.exists(filename):
        os.remove(filename)
        print(f"Deleted: {filename}")
    else:
        print(f"File not found: {filename}")