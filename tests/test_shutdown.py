import json
import unittest
from unittest.mock import MagicMock, patch

from app.web.shutdown import unload_ollama_models


class ShutdownTests(unittest.TestCase):
    @patch("app.web.shutdown.urlopen")
    def test_unload_posts_each_distinct_model_once(self, urlopen):
        response = MagicMock()
        response.status = 200
        urlopen.return_value.__enter__.return_value = response

        unloaded = unload_ollama_models(
            "http://127.0.0.1:11434/",
            ["qwen:7b", "qwen:7b", "other:3b"],
        )

        self.assertEqual(unloaded, ["qwen:7b", "other:3b"])
        self.assertEqual(urlopen.call_count, 2)

        first_request = urlopen.call_args_list[0].args[0]
        self.assertEqual(
            first_request.full_url,
            "http://127.0.0.1:11434/api/generate",
        )
        self.assertEqual(
            json.loads(first_request.data),
            {"model": "qwen:7b", "prompt": "", "keep_alive": 0},
        )


if __name__ == "__main__":
    unittest.main()
