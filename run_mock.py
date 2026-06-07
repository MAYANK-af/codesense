import os
import sys
from unittest.mock import MagicMock

# 1. Mock langchain_openai before it gets imported in agent/main.py
class MockChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass
    def invoke(self, messages):
        human_msg = messages[1].content if len(messages) > 1 else ""
        
        mock_content = """**Summary:** The changes in this file introduce several security vulnerabilities and styling issues.

**Issues Found:**
- 🔴 Critical: Hardcoded API key detected in the code (`api_key = "secret_api_key_12345"`).
- 🔴 Critical: Unsafe use of `eval()` detected. This allows execution of arbitrary code and is a major security risk.
- 🟡 Warning: Bare `except:` block detected. It's recommended to catch specific exceptions.
- 🟢 Suggestion: Function `login_user` lacks a docstring.
- 🟢 Suggestion: Debug `print()` statement detected. Use Python's `logging` module instead.

**Positive Notes:**
- The function implementation is straightforward."""
        
        class MockResponse:
            content = mock_content
        return MockResponse()

mock_langchain_openai = MagicMock()
mock_langchain_openai.ChatOpenAI = MockChatOpenAI
sys.modules['langchain_openai'] = mock_langchain_openai

# 2. Mock requests module to intercept GitHub API calls
import requests

def mock_get(url, *args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data
        @property
        def text(self):
            return str(self.json_data)
    
    if "pulls" in url and url.endswith("/files"):
        # Mock files list in the PR
        return MockResponse([
            {
                "filename": "auth_helper.py",
                "patch": "+def login_user(username, password):\n+    print(\"Attempting login...\")\n+    api_key = \"secret_api_key_12345\"\n+    eval(username)\n+    try:\n+        db.save(username)\n+    except:\n+        pass"
            }
        ], 200)
    elif "pulls" in url:
        # Mock open PR list
        return MockResponse([
            {
                "number": 42,
                "title": "Add login authentication handler"
            }
        ], 200)
    
    return MockResponse({}, 404)

def mock_post(url, *args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data
        @property
        def text(self):
            return str(self.json_data)

    if "comments" in url:
        payload = kwargs.get("json", {})
        print(f"\n📢 --- [MOCK INTERCEPT: POST TO GITHUB API] ---")
        print(f"URL: {url}")
        print(f"Comment Posted:\n{payload.get('body')}")
        print(f"-----------------------------------------------\n")
        return MockResponse({"status": "created"}, 201)
    
    return MockResponse({}, 404)

requests.get = mock_get
requests.post = mock_post

# 3. Setup mock environment variables so validation passes
os.environ["OPENAI_API_KEY"] = "mock-openai-key"
os.environ["GITHUB_TOKEN"] = "mock-github-token"
os.environ["GITHUB_REPO"] = "mock-owner/mock-repo"

# Add agent folder to path so tools are found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "agent")))

# 4. Import the main agent code and run it
from agent.main import run_agent

if __name__ == "__main__":
    run_agent()
