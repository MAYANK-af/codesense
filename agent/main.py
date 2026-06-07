import os
from dotenv import load_dotenv
from tools.diff_parser import get_open_prs, get_pr_diff
from tools.gh_commenter import post_review_comments
from tools.ast_analyser import analyse_code
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
GITHUB_REPO    = os.getenv("GITHUB_REPO")  # format: "owner/repo"

llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.2,
    api_key=OPENAI_API_KEY
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, "prompts", "review_prompt.txt")
with open(PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()

def review_pr(pr_number, diff, file_path):
    """Send diff to GPT-4 and get structured review feedback."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"File: {file_path}\n\nCode diff:\n{diff}")
    ]
    response = llm.invoke(messages)
    return response.content

def run_agent():
    print(f"🤖 CodeSense starting — monitoring repo: {GITHUB_REPO}")
    prs = get_open_prs(GITHUB_REPO, GITHUB_TOKEN)

    if not prs:
        print("No open PRs found.")
        return

    for pr in prs:
        pr_number = pr["number"]
        pr_title  = pr["title"]
        print(f"\n📋 Reviewing PR #{pr_number}: {pr_title}")

        diffs = get_pr_diff(GITHUB_REPO, pr_number, GITHUB_TOKEN)

        for file_path, diff_chunk in diffs.items():
            print(f"  → Analysing: {file_path}")

            # Static AST analysis first
            ast_notes = analyse_code(diff_chunk)

            # Send to LLM for deep review
            llm_review = review_pr(pr_number, diff_chunk, file_path)

            # Combine AST notes + LLM review
            full_comment = ""
            if ast_notes:
                full_comment += f"**Static Analysis Notes:**\n{ast_notes}\n\n"
            full_comment += f"**AI Review:**\n{llm_review}"

            # Post as a PR comment
            post_review_comments(
                repo=GITHUB_REPO,
                pr_number=pr_number,
                file_path=file_path,
                comment=full_comment,
                token=GITHUB_TOKEN
            )
            print(f"  ✅ Comment posted on {file_path}")

    print("\n✅ CodeSense review complete.")

if __name__ == "__main__":
    run_agent()
