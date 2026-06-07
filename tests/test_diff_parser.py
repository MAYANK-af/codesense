import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add agent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent")))

from tools.diff_parser import get_open_prs, get_pr_diff

class TestDiffParser(unittest.TestCase):
    @patch('tools.diff_parser.requests.get')
    def test_get_open_prs(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"number": 1, "title": "Test PR"}]
        mock_get.return_value = mock_response

        prs = get_open_prs("owner/repo", "token")
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["number"], 1)
        self.assertEqual(prs[0]["title"], "Test PR")

    @patch('tools.diff_parser.requests.get')
    def test_get_pr_diff(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"filename": "app.py", "patch": "+def main():\n+    print('hello')"},
            {"filename": "README.md", "patch": "+# README"},
            {"filename": "node_modules/lodash/index.js", "patch": "+// lodash"},
            {"filename": "package-lock.json", "patch": "+{}"},
            {"filename": "large_file.py", "patch": "+" * 30000}
        ]
        mock_get.return_value = mock_response

        diffs = get_pr_diff("owner/repo", 1, "token")
        # Should filter and only include supported file extensions (like .py, not .md)
        self.assertIn("app.py", diffs)
        self.assertNotIn("README.md", diffs)
        # Should exclude lock files & dependencies
        self.assertNotIn("node_modules/lodash/index.js", diffs)
        self.assertNotIn("package-lock.json", diffs)
        # Should exclude large files
        self.assertNotIn("large_file.py", diffs)
        self.assertEqual(diffs["app.py"], "+def main():\n+    print('hello')")

if __name__ == "__main__":
    unittest.main()
