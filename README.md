AgenticSec: AI-Driven DevSecOps Pipeline 🛡️🤖

AgenticSec is a localized, AI-powered pre-commit gate that shifts security to the absolute left of the software development lifecycle (SDLC).

Instead of waiting for cloud-based SAST tools to flag vulnerabilities during the CI/CD deployment phase, this tool uses the Google Gemini API to analyze source code locally. It not only identifies OWASP vulnerabilities but acts as an automated security engineer by generating secure, drop-in replacement code and breaking the build (sys.exit(1)) if critical flaws are detected.

⚡ Core Features

Dynamic File Ingestion: Point the CLI at any local Python script to scan it instantly.

Build-Breaker Gate: Parses structured JSON from the LLM. If a vulnerability is classified as High or Critical, the script terminates with a non-zero exit code, physically preventing vulnerable code from progressing.

Agentic Auto-Remediation: Reduces developer friction by generating context-aware, secure code patches directly in the terminal output.

🧠 Architecture Flow

graph LR
    A[Target Code] -->|Ingested via CLI| B(agentic_reviewer.py)
    B -->|Code Diff + Prompt| C{Gemini API}
    C -->|Strict JSON Output| D[Severity Parser]
    D -->|Low/Medium| E[Warn & Pass]
    D -->|High/Critical| F[sys.exit 1 + Remediation Code]


(Note: The above diagram renders natively in GitHub using Mermaid.js)

🛠️ Prerequisites & Installation

Python 3.9+ is required.

Clone this repository:

git clone https://github.com/yourusername/AgenticSec.git
cd AgenticSec


Install the required dependencies:

pip install google-genai


Obtain a free Gemini API Key from Google AI Studio and export it to your environment:

# For Linux/macOS
export GEMINI_API_KEY="your_api_key_here"

# For Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"


🚀 Usage

Run the scanner by passing a target file as an argument.

python agentic_reviewer.py <path_to_file.py>


Example: Catching a SQL Injection

If you run the scanner against a file containing a raw f-string SQL query, the build will break and output the following:

$ python agentic_reviewer.py src/bad_login.py

Scanning src/bad_login.py for vulnerabilities...

[Critical] SQL Injection on line 14: Unsanitized user input concatenated directly into SQL query string.

--- SUGGESTED FIX ---
def login(username, password):
    # Use parameterized queries to prevent SQL injection
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    execute_db(query, (username, password))
---------------------

❌ CRITICAL VULNERABILITY FOUND. FAILING THE BUILD.


🛣️ Roadmap

[x] Local CLI File Ingestion

[x] JSON Schema Enforcement & Severity Parsing

[x] Build Breaker / Exit Codes

[ ] Integration with GitHub Actions for automated PR comments

[ ] Repository-wide context scanning using RAG

🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
