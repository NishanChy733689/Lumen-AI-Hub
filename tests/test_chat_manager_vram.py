import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pages.chat_manager import OllamaChatManager


class VRAMSelectionTests(unittest.TestCase):
    def test_uses_quantized_variant_when_vram_limit_exceeded(self):
        manager = OllamaChatManager.__new__(OllamaChatManager)

        resolved = manager._select_model_variant(
            "smollm2:135m", vram_used_gb=2.1, limit_gb=2.0
        )

        self.assertEqual(resolved, "smollm2:135m-q4")

    def test_keeps_full_precision_when_vram_is_within_limit(self):
        manager = OllamaChatManager.__new__(OllamaChatManager)

        resolved = manager._select_model_variant(
            "smollm2:135m", vram_used_gb=1.8, limit_gb=2.0
        )

        self.assertEqual(resolved, "smollm2:135m")


if __name__ == "__main__":
    unittest.main()
