import os
import hmac
import hashlib
import json
import sys
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from dotenv import load_dotenv

# Add current folder to path so tools are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load tools
from tools.diff_parser import get_pr_diff
from tools.gh_commenter import post_review_comments
from tools.ast_analyser import analyse_code
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

load_dotenv()

app = FastAPI(
    title="CodeSense Webhook Server",
    description="Listen to GitHub Webhooks and trigger AI pull request reviews asynchronously."
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# Load system prompt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "review_prompt.txt")
if os.path.exists(PROMPT_PATH):
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
else:
    SYSTEM_PROMPT = "You are CodeSense, an AI code reviewer."

def run_review_pipeline(repo: str, pr_number: int):
    print(f"[BACKGROUND TASK] Starting review for {repo} PR #{pr_number}...")
    
    if not OPENAI_API_KEY or not GITHUB_TOKEN:
        print("[ERROR] Missing OPENAI_API_KEY or GITHUB_TOKEN in environment variables.")
        return

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.2,
        api_key=OPENAI_API_KEY
    )

    # Fetch diffs
    diffs = get_pr_diff(repo, pr_number, GITHUB_TOKEN)
    if not diffs:
        print(f"[INFO] No supported files found in diff for PR #{pr_number}")
        return

    for file_path, diff_chunk in diffs.items():
        print(f"  -> Analysing: {file_path}")

        # Static AST analysis
        ast_notes = analyse_code(diff_chunk)

        # AI Review
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"File: {file_path}\n\nCode diff:\n{diff_chunk}")
        ]
        response = llm.invoke(messages)
        llm_review = response.content

        # Combine comments
        full_comment = ""
        if ast_notes:
            full_comment += f"**Static Analysis Notes:**\n{ast_notes}\n\n"
        full_comment += f"**AI Review:**\n{llm_review}"

        # Post to GitHub
        post_review_comments(
            repo=repo,
            pr_number=pr_number,
            file_path=file_path,
            comment=full_comment,
            token=GITHUB_TOKEN
        )
        print(f"  ✅ Comment posted on {file_path}")

    print(f"[BACKGROUND TASK] Review completed for {repo} PR #{pr_number}.")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "agent": "CodeSense Webhook Server",
        "webhook_signature_verified": WEBHOOK_SECRET is not None
    }

@app.post("/webhook")
async def handle_webhook(
      request: Request,
      background_tasks: BackgroundTasks,
      x_github_event: str = Header(None),
      x_hub_signature_256: str = Header(None)
):
    body = await request.body()
    
    # Verify signature if secret is configured
    if WEBHOOK_SECRET:
        if not x_hub_signature_256:
            raise HTTPException(status_code=401, detail="Missing signature header")
        mac = hmac.new(WEBHOOK_SECRET.encode(), msg=body, digestmod=hashlib.sha256)
        expected_sig = "sha256=" + mac.hexdigest()
        if not hmac.compare_digest(expected_sig, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "pull_request":
        return {"status": "skipped", "message": f"Unsupported event: {x_github_event}"}

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    action = payload.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return {"status": "skipped", "message": f"Action '{action}' is not audited."}

    pr_number = payload.get("number")
    repo = payload.get("repository", {}).get("full_name")

    if not pr_number or not repo:
        raise HTTPException(status_code=400, detail="Missing PR number or repository in payload")

    # Schedule the review pipeline to run in the background
    background_tasks.add_task(run_review_pipeline, repo, pr_number)

    return {
        "status": "queued",
        "message": f"Review queued for {repo} PR #{pr_number} (Action: {action})"
    }
