import os
from pathlib import Path

SENSITIVE_FILES = [".env", "ssh_keys.enc", "config.json", "permissions_config.json"]


def check_file_permissions(filepath: str) -> tuple[bool, str]:
    try:
        st = os.stat(filepath)
        mode = st.st_mode
        insecure = mode & 0o077
        return insecure == 0, oct(mode)[-3:]
    except FileNotFoundError:
        return False, "missing"


def audit_files() -> list[dict]:
    results = []
    for f in SENSITIVE_FILES:
        secure, mode = check_file_permissions(f)
        if mode == "missing":
            status = "missing"
            recommendation = "Create file if needed"
        elif secure:
            status = "secure"
            recommendation = ""
        else:
            status = "insecure"
            recommendation = f"Run: chmod 600 {f}"
        results.append({
            "file": f,
            "status": status,
            "permissions": mode,
            "recommendation": recommendation,
        })
    return results


def _extract_deps(content: str) -> list[str]:
    import re
    return re.findall(r'"([^"]+)"', content.split("dependencies")[1].split("]")[0]) if "dependencies" in content else []


def audit_dependencies() -> list[str]:
    warnings: list[str] = []
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        warnings.append("pyproject.toml not found")
        return warnings

    content = pyproject.read_text(encoding="utf-8")
    deps = _extract_deps(content)
    for dep in deps:
        if "==" not in dep:
            warnings.append(f"Unpinned dependency: {dep}")

    return warnings


def run_audit() -> dict:
    return {
        "files": audit_files(),
        "dependencies": audit_dependencies(),
    }
