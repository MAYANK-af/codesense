import sys
import os
import unittest

# Add agent directory to sys.path so we can import tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent")))

from tools.ast_analyser import analyse_code

class TestASTAnalyser(unittest.TestCase):
    def test_detect_secrets(self):
        diff = "+api_key = 'secret_value_123'\n"
        findings = analyse_code(diff)
        self.assertIn("Possible hardcoded secret detected", findings)

    def test_detect_eval(self):
        diff = "+eval('print(1)')\n"
        findings = analyse_code(diff)
        self.assertIn("`eval()` detected", findings)

    def test_detect_bare_except(self):
        diff = "+try:\n+    do_something()\n+except:\n+    pass"
        findings = analyse_code(diff)
        self.assertIn("Bare `except:` clause detected", findings)

    def test_detect_print_statement(self):
        # Needs to be > 5 added lines to trigger print check
        diff = "+print('test 1')\n+print('test 2')\n+print('test 3')\n+print('test 4')\n+print('test 5')\n+print('test 6')\n"
        findings = analyse_code(diff)
        self.assertIn("Debug logging statements found", findings)

    def test_detect_javascript_console_log(self):
        diff = "+console.log('test 1')\n+console.log('test 2')\n+console.log('test 3')\n+console.log('test 4')\n+console.log('test 5')\n+console.log('test 6')\n"
        findings = analyse_code(diff)
        self.assertIn("Debug logging statements found", findings)

    def test_detect_cpp_cout(self):
        diff = "+std::cout << 'test 1'\n+std::cout << 'test 2'\n+std::cout << 'test 3'\n+std::cout << 'test 4'\n+std::cout << 'test 5'\n+std::cout << 'test 6'\n"
        findings = analyse_code(diff)
        self.assertIn("Debug logging statements found", findings)

    def test_detect_missing_docstring_indented(self):
        # Testing the textwrap.dedent fix for indented code
        diff = "+    def some_function():\n+        return 42\n"
        findings = analyse_code(diff)
        self.assertIn("missing a docstring", findings)

    def test_function_length(self):
        # A function with >50 lines
        lines = ["+def long_function():"]
        for i in range(55):
            lines.append(f"+    print({i})")
        diff = "\n".join(lines)
        findings = analyse_code(diff)
        self.assertIn("lines long", findings)

if __name__ == "__main__":
    unittest.main()
