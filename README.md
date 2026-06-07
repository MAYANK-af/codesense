# 🤖 CodeSense — AI Code Review Agent

An autonomous AI agent that reviews GitHub Pull Requests and posts detailed, inline code review comments — automatically. No human reviewer needed for the first pass.

---

## 🎯 What it does

- Connects to any GitHub repository
- Reads new Pull Requests automatically
- Analyses the code diff for:
  - 🐛 Logic errors
  - 🎨 Style issues (naming, readability)
  - 🔒 Security vulnerabilities
  - ✅ Best practice suggestions
- Posts comments **directly on the specific lines** in the PR
- Works like a senior developer doing a first-pass review

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10 |
| AI Framework | LangChain |
| LLM | OpenAI GPT-4 API |
| Integrations | GitHub REST API (PyGithub) |
| Agent Design | ReAct Agent Pattern |

---

## 📁 Project Structure

```
codesense/
├── agent/
│   ├── main.py           # Agent entry point
│   ├── tools/
│   │   ├── diff_parser.py     # Reads and chunks PR diffs
│   │   ├── ast_analyser.py    # AST-level code understanding
│   │   └── gh_commenter.py    # Posts comments via GitHub API
│   └── prompts/
│       └── review_prompt.txt  # System prompt for the LLM
├── .env.example          # Template for secrets (never push .env!)
├── requirements.txt
└── README.md
```

---

## ⚙️ How to Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/mayankyadav/codesense.git
cd codesense
```

**2. Set up your secrets**
```bash
cp .env.example .env
```
Open `.env` and fill in:
```
OPENAI_API_KEY=your_openai_key_here
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/repo-name
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the agent (CLI)**
```bash
python agent/main.py
```

---

## ⚙️ Entrypoints & Running Modes

CodeSense can be run in four different modes depending on your deployment target.

### 1. Reusable GitHub Action (CI/CD)
You can include CodeSense in your repository's workflow to run automatically on every Pull Request. Create `.github/workflows/codesense.yml`:

```yaml
name: AI Pull Request Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run CodeSense
        uses: YOUR_USERNAME/codesense@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
```

### 2. FastAPI Webhook Server (Real-Time Web API)
To deploy CodeSense as a persistent web service that listens to GitHub webhooks:

```bash
# Start the webhook server
python -m uvicorn agent.webhook_server:app --host 0.0.0.0 --port 8000
```
- Set up a GitHub webhook pointing to `http://your-server-ip:8000/webhook`.
- Choose the `Pull requests` event.
- Secure it by setting `GITHUB_WEBHOOK_SECRET` in your `.env` for HMAC signature validation.

### 3. Local Web Dashboard (Sandbox)
To launch the interactive dashboard and code review sandbox in your browser:
```bash
python run_frontend.py
```
This runs a local HTTP server at `http://127.0.0.1:8080/index.html` with pre-loaded code templates and custom input areas.

### 4. Docker Container
Build and run the containerized agent locally:
```bash
docker build -t codesense-agent .
docker run --env-file .env codesense-agent
```

---

## 🧪 Running Unit Tests

We have a comprehensive test suite (12 tests) verifying AST analysis (with indentation support), diff parsing exclusions, and commenter API request headers:
```bash
python -m unittest discover -s tests
```

---

## 🔐 Important — Never push your API keys

The `.env` file is already in `.gitignore`. Never remove it from there. Get your keys from:
- OpenAI key → platform.openai.com
- GitHub token → GitHub → Settings → Developer Settings → Personal Access Tokens

---

## 🔮 Future Plans

- [ ] Support for GitLab and Bitbucket
- [ ] Slack notification on review completion
- [x] Webhook server for real-time webhook audits
- [x] Dockerization & packaging as a native GitHub Action

---

## 👤 Author

**Mayank Yadav**  
B.Tech Computer Science — Manipal University Jaipur  
my1220301@gmail.com
