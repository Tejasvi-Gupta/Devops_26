"""
Detection logic: given a tool name, figure out if it's installed and what
version it is.

Design: each known tool has a small config (command + a regex to pull the
version number out of that command's output). This covers the common case
without needing per-tool special-casing everywhere else in the agent.
"""
import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class DetectionResult:
    found: bool
    version: str | None       # e.g. "3.11.4", or None if not found/unparseable
    raw_output: str | None    # useful for debugging, not sent to backend
    error: str | None = None  # set if the check itself failed (permissions, etc.)


# Built-in detection recipes for common tools. version_regex must have
# exactly one capture group containing the version string.
TOOL_CHECKS: dict[str, dict] = {
    "python": {"command": ["python", "--version"], "version_regex": r"Python (\d+\.\d+\.\d+)"},
    "node": {"command": ["node", "--version"], "version_regex": r"v(\d+\.\d+\.\d+)"},
    "git": {"command": ["git", "--version"], "version_regex": r"git version (\d+\.\d+\.\d+)"},
    "docker": {"command": ["docker", "--version"], "version_regex": r"Docker version (\d+\.\d+\.\d+)"},
    "npm": {"command": ["npm", "--version"], "version_regex": r"(\d+\.\d+\.\d+)"},
}


def detect_tool(tool_name: str, version_check_cmd: str | None = None) -> DetectionResult:
    """
    Detect whether `tool_name` is installed and return its version.

    If `version_check_cmd` is provided (from the backend's Requirement),
    it overrides the built-in recipe -- this lets instructors support
    tools the agent doesn't know about yet. Otherwise falls back to
    TOOL_CHECKS, and if the tool isn't in there either, reports an error
    rather than silently guessing.
    """
    tool_name_lower = tool_name.lower()

    if version_check_cmd:
        return _run_custom_check(version_check_cmd)

    recipe = TOOL_CHECKS.get(tool_name_lower)
    if not recipe:
        return DetectionResult(
            found=False,
            version=None,
            raw_output=None,
            error=f"No built-in check for '{tool_name}' and no version_check_cmd provided",
        )

    return _run_recipe_check(tool_name_lower, recipe)


def _run_recipe_check(tool_name: str, recipe: dict) -> DetectionResult:
    command = recipe["command"]

    # Quick existence check first (cheap, avoids spawning a process for
    # tools that clearly aren't on PATH at all).
    if shutil.which(command[0]) is None:
        return DetectionResult(found=False, version=None, raw_output=None)

    try:
        proc = subprocess.run(
            command, capture_output=True, text=True, timeout=10
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return DetectionResult(found=False, version=None, raw_output=None, error=str(e))

    output = (proc.stdout or "") + (proc.stderr or "")
    match = re.search(recipe["version_regex"], output)
    if match:
        return DetectionResult(found=True, version=match.group(1), raw_output=output)

    # Binary exists and ran, but we couldn't parse a version from it.
    return DetectionResult(
        found=True, version=None, raw_output=output,
        error="Found the tool but could not parse its version",
    )


def _run_custom_check(version_check_cmd: str) -> DetectionResult:
    """Run an instructor-provided shell command string and try to pull
    a version-looking token (digits.digits[.digits]) out of the output."""
    try:
        proc = subprocess.run(
            version_check_cmd, shell=True, capture_output=True, text=True, timeout=10
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return DetectionResult(found=False, version=None, raw_output=None, error=str(e))

    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 and not output.strip():
        return DetectionResult(found=False, version=None, raw_output=output)

    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
    version = match.group(1) if match else None
    return DetectionResult(found=(version is not None), version=version, raw_output=output)
