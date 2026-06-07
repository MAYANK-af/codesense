import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add agent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent")))

from tools.gh_commenter import post_review_comments

class TestGHCommenter(unittest.TestCase):
    @patch('tools.gh_commenter.requests.post')
    def test_post_review_comments_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        res = post_review_comments("owner/repo", 42, "app.py", "Looks good!", "token")
        self.assertTrue(res)
        mock_post.assert_called_once()

    @patch('tools.gh_commenter.requests.post')
    def test_post_review_comments_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        res = post_review_comments("owner/repo", 42, "app.py", "Looks good!", "token")
        self.assertFalse(res)
        mock_post.assert_called_once()

if __name__ == "__main__":
    unittest.main()
