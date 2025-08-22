import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Class to check code quality
class CodeQualityChecker:
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.python_files: List[Path] = []
        self.issues: List[Dict] = []

    def find_python_files(self) -> None:
        """Find all Python files in the project directory."""
        self.python_files = list(self.project_dir.rglob("*.py"))

    def check_file(self, file_path: Path) -> List[Dict]:
        """Check a single Python file for code quality issues."""
        issues = []
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
            tree = ast.parse(content, filename=str(file_path))

            # Check for various issues
            issues.extend(self._check_imports(content, lines))
            issues.extend(self._check_ast(tree, lines))

        return issues

    def _check_imports(self, content: str, lines: List[str]) -> List[Dict]:
        """Check for import-related issues."""
        issues = []
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')):
                if '  ' in line:
                    issues.append({
                        "line": i + 1,
                        "issue": "Multiple spaces in import statement"
                    })
        return issues

    def _check_ast(self, tree: ast.AST, lines: List[str]) -> List[Dict]:
        """Check for AST-related issues."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not any(isinstance(e, ast.Expr) and isinstance(e.value, ast.Str) for e in node.body):
                    issues.append({
                        "line": node.lineno,
                        "issue": "Missing docstring in function"
                    })
        return issues

    def check_all_files(self) -> None:
        """Check all Python files for code quality issues."""
        self.find_python_files()
        for file_path in self.python_files:
            self.issues.extend(self.check_file(file_path))

    def generate_report(self) -> str:
        """Generate a report of all code quality issues found."""
        report_lines = [f"{issue['line']}: {issue['issue']}" for issue in self.issues]
        return "\n".join(report_lines)

# Main function to run code quality checks
def main():
    """Main function to run code quality checks."""
    checker = CodeQualityChecker()
    checker.check_all_files()
    report = checker.generate_report()
    if report:
        print("Code Quality Issues Found:")
        print(report)
    else:
        print("No code quality issues found.")

if __name__ == '__main__':
    main()
