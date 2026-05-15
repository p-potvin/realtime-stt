import subprocess
import os
import sys
from unittest.mock import MagicMock
import types

# Mock everything needed for parakeet_wrapper to import
sys.modules["torch"] = MagicMock()
sys.modules["numpy"] = MagicMock()

nemo = types.ModuleType("nemo")
nemo.collections = types.ModuleType("collections")
nemo.collections.asr = types.ModuleType("asr")
nemo.collections.asr.models = MagicMock()
sys.modules["nemo"] = nemo
sys.modules["nemo.collections"] = nemo.collections
sys.modules["nemo.collections.asr"] = nemo.collections.asr

import stt_engine.parakeet_wrapper as pw

def test_popen_not_patched_globally(os_name):
    print(f"Testing for OS: {os_name}")
    os.name = os_name # Simulate OS

    # Refresh current Popen
    current_popen = subprocess.Popen

    # Inside context manager
    with pw.hush_subprocess():
        patched_popen = subprocess.Popen
        if os_name == 'nt':
            if current_popen == patched_popen:
                print(f"FAILED: subprocess.Popen NOT patched inside hush_subprocess on {os_name}")
                return False
            else:
                print(f"SUCCESS: subprocess.Popen patched inside hush_subprocess on {os_name}")
        else:
            if current_popen != patched_popen:
                print(f"FAILED: subprocess.Popen patched inside hush_subprocess on {os_name}")
                return False
            else:
                print(f"SUCCESS: subprocess.Popen NOT patched on {os_name} (expected)")

    # After context manager, it should be restored
    post_popen = subprocess.Popen
    if current_popen != post_popen:
        print(f"FAILED: subprocess.Popen NOT restored after hush_subprocess on {os_name}")
        return False
    else:
        print(f"SUCCESS: subprocess.Popen restored after hush_subprocess on {os_name}")

    return True

if __name__ == "__main__":
    original_os_name = os.name
    try:
        success = test_popen_not_patched_globally('posix') and test_popen_not_patched_globally('nt')
    finally:
        os.name = original_os_name

    if success:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Tests failed!")
        sys.exit(1)
