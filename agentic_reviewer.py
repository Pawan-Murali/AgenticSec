"""
Agentic Security Reviewer — CI/CD Gate
Uses the Gemini API (google-genai SDK) to perform an automated AppSec review
of a target source file and fails the build on High/Critical findings.
"""

import sys
import json
import time
import argparse
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# ---------------------------------------------------------------------------
# System prompt that turns Gemini into an AppSec reviewer
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """\
You are an expert Application Security (AppSec) engineer performing a \
security code review with auto-remediation.

Analyze the provided Python code for security vulnerabilities. Return ONLY \
a JSON object with a single key called "vulnerabilities". The value must be \
a list of objects, each containing exactly these keys:

- "type": short name of the vulnerability (e.g. "SQL Injection")
- "line_number": approximate line number in the snippet (integer)
- "description": a clear explanation of the flaw
- "severity": one of "Low", "Medium", "High", "Critical"
- "remediation_code": the exact corrected Python code that replaces the \
  vulnerable lines to fix this specific issue. Include only the relevant \
  function, route, or block — not the entire file. The code must be valid \
  Python, ready to copy-paste.

If no vulnerabilities are found, return: {"vulnerabilities": []}
Do NOT include markdown fences, commentary, or any text outside the JSON object.
"""

USER_PROMPT_TEMPLATE = """\
Review the following code for security vulnerabilities:

--- BEGIN CODE ---
{code}
--- END CODE ---
"""

# Severities that should break the build
BLOCKING_SEVERITIES = {"High", "Critical"}


def read_target_file(filepath: str) -> str:
    """Open and return the contents of the target file.

    Exits with an error message if the file does not exist or cannot be read.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌  Error: File not found — {filepath}")
        sys.exit(1)
    except PermissionError:
        print(f"❌  Error: Permission denied — {filepath}")
        sys.exit(1)
    except OSError as e:
        print(f"❌  Error reading file — {e}")
        sys.exit(1)


def review_code(
    code: str,
    model_name: str = "gemini-3.8-flash",
    max_retries: int = 3,
    base_delay: float = 5.0,
) -> dict:
    """Send *code* to the Gemini API for an AppSec review.

    Retries with exponential back-off on transient server errors (503, 429).
    Returns the parsed JSON object with a 'vulnerabilities' key.
    """
    client = genai.Client()  # picks up GEMINI_API_KEY from env

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=USER_PROMPT_TEMPLATE.format(code=code),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
            if not response.text:
                if attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    print(f"⚠️  Empty response (attempt {attempt}/{max_retries}). Retrying in {delay:.0f}s …")
                    time.sleep(delay)
                    continue
                else:
                    print("❌  Model returned an empty response after all retries.")
                    print("    This may be caused by safety filters or rate limiting.")
                    sys.exit(1)
            result = json.loads(response.text)
            return result
        except genai_errors.ServerError as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                print(f"⏳  Server busy (attempt {attempt}/{max_retries}). Retrying in {delay:.0f}s …")
                time.sleep(delay)
            else:
                print(f"❌  Server error after {max_retries} attempts: {e}")
                sys.exit(1)
        except genai_errors.ClientError as e:
            print(f"❌  API client error: {e}")
            sys.exit(1)


def print_findings(vulnerabilities: list[dict]) -> None:
    """Pretty-print the security findings with remediation code to the console."""
    if not vulnerabilities:
        print("✅  No vulnerabilities found.")
        return

    print(f"🔍  Found {len(vulnerabilities)} issue(s):\n")
    for i, vuln in enumerate(vulnerabilities, start=1):
        severity = vuln.get("severity", "Unknown")
        vtype = vuln.get("type", "N/A")
        line = vuln.get("line_number", "?")
        desc = vuln.get("description", "")
        fix = vuln.get("remediation_code", "")

        print(f"{'=' * 60}")
        print(f"  [{i}] {severity} — {vtype}  (line ~{line})")
        print(f"  Description: {desc}")
        if fix:
            print(f"\n  💡 Remediation:")
            print(f"  {'-' * 56}")
            for code_line in fix.splitlines():
                print(f"    {code_line}")
            print(f"  {'-' * 56}")
    print(f"{'=' * 60}")


def gate_check(vulnerabilities: list[dict]) -> None:
    """Act as a CI/CD gate — exit(1) if any High or Critical issues exist."""
    blockers = [
        v for v in vulnerabilities
        if v.get("severity") in BLOCKING_SEVERITIES
    ]

    if blockers:
        print(f"\n🚨  CI/CD GATE FAILURE — {len(blockers)} blocking issue(s) found:")
        for v in blockers:
            print(f"   • [{v.get('severity')}] {v.get('type')} (line ~{v.get('line_number', '?')})")
        print("\n❌  Build failed. Fix all High/Critical vulnerabilities before merging.")
        sys.exit(1)
    else:
        print("\n✅  CI/CD GATE PASSED — no High or Critical vulnerabilities detected.")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agentic Security Reviewer — CI/CD gate that scans a Python file for vulnerabilities using Gemini."
    )
    parser.add_argument(
        "file",
        help="Path to the Python source file to review.",
    )
    args = parser.parse_args()

    # Set the GEMINI_API_KEY environment variable before running,
    # or uncomment below and paste your key directly:
    # import os
    # os.environ["GEMINI_API_KEY"] = "YOUR_API_KEY"

    code = read_target_file(args.file)
    result = review_code(code)
    vulnerabilities = result.get("vulnerabilities", [])

    print_findings(vulnerabilities)
    gate_check(vulnerabilities)
