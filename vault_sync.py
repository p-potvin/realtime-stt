import os
import subprocess
import sys
import re

def is_safe_input(s):
    if not s or s.startswith("-"):
        return False
    return bool(re.match(r"^[\w\-\./:@~+=]+$", s))

def sync_vault_dependencies():
    """
    VaultWares custom package manager for Git Submodules.
    Reads VAULT_DEPENDENCIES.txt and ensures all submodules are synchronized.
    """
    manifest_path = "VAULT_DEPENDENCIES.txt"
    
    if not os.path.exists(manifest_path):
        print(f"[-] {manifest_path} not found. Skipping vault sync.")
        return

    print("[*] Synchronizing VaultWares dependencies...")
    
    with open(manifest_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            folder, url, branch = line.split()
            if not (is_safe_input(folder) and is_safe_input(url) and is_safe_input(branch)):
                print(f"[-] Unsafe input detected in line: '{line}'")
                continue

            print(f"[*] Ensuring dependency: {folder} from {url} ({branch})")

            # Check if directory exists
            if not os.path.exists(folder):
                print(f"[*] Adding new submodule {folder}...")
                subprocess.run(["git", "submodule", "add", "-b", branch, "--", url, folder], check=True)
            else:
                print(f"[*] Updating existing submodule {folder}...")
                subprocess.run(["git", "submodule", "update", "--init", "--remote", "--", folder], check=True)

        except ValueError:
            print(f"[-] Malformed line in {manifest_path}: '{line}'")
        except subprocess.CalledProcessError as e:
            print(f"[-] Git error while syncing {folder}: {e}")

if __name__ == "__main__":
    sync_vault_dependencies()
