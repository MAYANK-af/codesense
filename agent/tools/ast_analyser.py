import ast
import re

def analyse_code(diff_chunk):
    """
    Extract added lines from diff and run basic AST + pattern checks.
    Returns a string of findings, or empty string if none.
    """
    added_lines = []
    for line in diff_chunk.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])  # strip the leading +

    import textwrap
    code = textwrap.dedent("\n".join(added_lines))
    findings = []

    # ── Pattern-based checks ──────────────────────────
    # Hardcoded secrets
    secret_patterns = [
        r'(?i)(password|secret|api_key|token)\s*=\s*["\'][^"\']{4,}["\']',
        r'(?i)Authorization:\s*["\']Bearer\s+[A-Za-z0-9\-_\.]+["\']',
    ]
    for pattern in secret_patterns:
        if re.search(pattern, code):
            findings.append("⚠️ **Possible hardcoded secret detected.** Avoid storing credentials directly in code — use environment variables instead.")
            break

    # eval() usage
    if re.search(r'\beval\s*\(', code):
        findings.append("⚠️ **`eval()` detected.** This is a security risk — avoid using `eval()` as it can execute arbitrary code.")

    # Debug print/log statements left in
    log_pattern = r'\b(print|console\.log|System\.out\.print(ln)?)\s*\(|std::cout\s*<<'
    if re.search(log_pattern, code) and len(added_lines) > 5:
        findings.append("ℹ️ **Debug logging statements found.** Consider replacing print, console.log, System.out, or std::cout with proper logging frameworks in production code.")

    # Bare except
    if re.search(r'except\s*:', code):
        findings.append("⚠️ **Bare `except:` clause detected.** Always catch specific exceptions (e.g. `except ValueError:`) for better error handling.")

    # ── AST checks (Python only) ──────────────────────
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # Functions with no docstring
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                    findings.append(f"ℹ️ Function `{node.name}()` is missing a docstring.")
            # Very long functions (>50 lines)
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno
                if func_lines > 50:
                    findings.append(f"ℹ️ Function `{node.name}()` is {func_lines} lines long — consider breaking it into smaller functions.")
    except SyntaxError:
        pass  # Not Python or incomplete snippet

    return "\n".join(findings)
