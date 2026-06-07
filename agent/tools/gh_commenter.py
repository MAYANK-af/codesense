import requests

def post_review_comments(repo, pr_number, file_path, comment, token):
    """Post a general PR review comment (not inline) via GitHub API."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CodeSense-CodeReviewAgent"
    }
    body = f"### 🤖 CodeSense Review — `{file_path}`\n\n{comment}"
    payload = {"body": body}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        return True
    else:
        print(f"Failed to post comment: {response.status_code} — {response.text}")
        return False
