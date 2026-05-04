import sys
import unittest.mock as mock
import types

sys.modules['soundcard'] = types.SimpleNamespace()

import unittest
from tests.test_audio_flow import TestAudioFlow

if __name__ == "__main__":
    unittest.main()
