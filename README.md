🛡️ AgenticSec: AI-Driven Code Reviewer

🌟 Highlights

Fully Localized: Runs directly on your machine as a Command Line Interface (CLI) tool.

Agentic Auto-Remediation: Doesn't just complain about bugs; it writes the secure code patch to fix them.

Build-Breaker Gate: Automatically halts pipelines (Exit 1) on High or Critical vulnerabilities to protect your main branch.

Lightweight: No heavy infrastructure or containers, just Python and the Gemini API.

ℹ️ Overview

AgenticSec is a fast, AI-powered security scanner designed to shift DevSecOps to the absolute left. Instead of waiting for a static vulnerability scan in the cloud, this tool acts as a senior AppSec engineer living right inside your terminal.

By analyzing local code files using Google's Gemini LLM, it catches Open Worldwide Application Security Project (OWASP) Top 10 vulnerabilities (like SQL injections and logic flaws) before they are even committed. It is designed to be frictionless for developers: if it breaks your build, it immediately hands you the exact code snippet needed to fix it.

✍️ Author

I'm Pawan Murali, and I created this project to demonstrate how generative AI can be integrated into traditional CI/CD pipelines to dramatically accelerate developer velocity while enforcing strict security postures.

⬇️ Installation

This tool requires Python 3.9+ and is completely cross-platform.

Install the required Google GenAI SDK:
pip install google-generativeai

Set your free Gemini API key as an environment variable:
# For macOS/Linux
export GEMINI_API_KEY="your_api_key_here"
# For Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"


🚀 Usage
Point the script at any vulnerable Python file on your machine to scan it and generate secure remediation code.
python agentic_reviewer.py target_file.py


🏗️ Architecture
Here is the data flow:
```mermaid
    A["Target Python Script"] --> B["Local CLI Ingestion (argparse)"]
    B --> C["Gemini API (google-genai)"]
    C --> D["Structured JSON Analysis"]
    
    D --> E{"Severity Assessment"}
    
    E -->|"Severity: Low / Medium"| F["Report Warnings & Exit 0"]
    E -->|"Severity: High / Critical"| G["Trigger Build Breaker (Exit 1)"]
    
    G --> H["Output Remediation Code Patch"]
    F --> I["Pipeline Passes"]
```
