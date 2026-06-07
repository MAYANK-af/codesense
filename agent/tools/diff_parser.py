import requests

def get_open_prs(repo, token):
    """Fetch all open pull requests from a GitHub repo."""
    url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CodeSense-CodeReviewAgent"
    }
    response = requests.get(url, headers=headers, params={"state": "open"})
    if response.status_code != 200:
        print(f"Error fetching PRs: {response.status_code} — {response.text}")
        return []
    return response.json()

def get_pr_diff(repo, pr_number, token):
    """
    Fetch the diff for a specific PR.
    Returns a dict: { file_path: diff_chunk }
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CodeSense-CodeReviewAgent"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching diff: {response.status_code}")
        return {}

    files = response.json()
    diffs = {}

    SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c"}

    EXCLUDED_PATTERNS = {"node_modules", "venv", ".venv", "dist", "build", "migrations", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

    for f in files:
        filename = f.get("filename", "")
        
        # Skip excluded patterns and directory names
        if any(pat in filename for pat in EXCLUDED_PATTERNS):
            print(f"  -> Skipping excluded file: {filename}")
            continue

        ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in SUPPORTED_EXTENSIONS:
            continue
            
        patch = f.get("patch", "")
        if len(patch) > 25000:
            print(f"  -> Skipping {filename} - diff is too large ({len(patch)} chars)")
            continue

        if patch:
            # Only take first 3000 chars per file to stay within token limits
            diffs[filename] = patch[:3000]

    return diffs
