import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time
import json
import re

URLS = [
    "https://www.ibm.com/docs/en/ztpf",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=programming-ztpf-conventions",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=applications-programming",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=reference-commands",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=macros-z-tpf-macro-reference",
    "https://www.ibm.com/docs/en/ztpf/1.1.2024?topic=apis-rexx",
    "https://www.ibm.com/docs/en/ztpf/1.1.2024?topic=tpf-operations-server",
    "https://www.ibm.com/docs/en/ztpf/1.1.2026?topic=components-rexx-automation-variation-environment-raven",
    "https://www.ibm.com/docs/en/ztpf/1.1.2024?topic=information-overview",
    "https://www.ibm.com/docs/en/ztpf/1.1.2024?topic=server-raven-programmers-guide",
    "https://www.ibm.com/docs/en/ztpf/1.1.2024?topic=guide-general",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=overview-raven-other-automation-techniques",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=information-programming-requirements",
    "https://www.ibm.com/docs/en/ztpfdf/1.1.2025",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=services-file-system",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=services-memory-management",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=processing-entry-control-blocks",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=programs-ztpf-loader",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=debugging-application-programs",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=overview-ztpf-system",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=utilities-ztpf-utilities",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=services-database-functions",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=programming-assembler-language",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=reference-system-error-messages",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=monitoring-performance",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=interfaces-apis",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=operations-system-administration",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=concepts-z-tpfdf",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=programming-reentrant-applications",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=overview-ecb-processing",
    "https://www.ibm.com/docs/en/ztpf/1.1.2025?topic=reference-z-commands",
    "https://www.ibm.com/docs/en/zos/latest?topic=rexx-restructured-extended-executor",
    "https://www.ibm.com/docs/en/zos/latest?topic=commands-rexx",
    "https://www.ibm.com/docs/en/zos/latest?topic=functions-built-in",
    "https://www.ibm.com/docs/en/zos/latest?topic=language-parsing-data-rexx",
    "https://www.ibm.com/docs/en/zos/latest?topic=language-control-instructions-rexx",
    "https://www.ibm.com/docs/en/zos/latest?topic=language-functions-subroutines-rexx",
    "https://www.ibm.com/docs/en/zos/latest?topic=language-debugging-rexx-programs",
    "https://www.ibm.com/docs/en/zos/latest?topic=editor-edit-macros-rexx",
]

def fetch_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Extract main content if possible, otherwise body
            main = soup.find('main') or soup.find('div', role='main') or soup.body
            if not main:
                return ""
            # Clean up script/style
            for tag in main(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            text = main.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            return f"--- SOURCE: {url} ---\n{text}\n\n"
        return ""
    except Exception as e:
        print(f"Failed {url}: {e}")
        return ""

print("Fetching documentation...")
all_text = ""
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(fetch_url, URLS)
    for res in results:
        all_text += res

# Save raw text
with open("backend/training/data/docs_raw.txt", "w", encoding="utf-8") as f:
    f.write(all_text)

print(f"Saved {len(all_text)} chars of raw documentation.")

# Generate summary using Ollama Llama 3.3 or Qwen to extract key principles
print("Generating compressed knowledge base using Ollama...")
PROMPT = """You are an expert IBM z/TPF and REXX engineer.
Read the following raw documentation extracts and produce a comprehensive, structured knowledge base.
Focus on:
1. z/TPF programming conventions and best practices.
2. Important z/TPF Macros (e.g. ENTER, EXITC, FILEC, FINDA, GETCC, RELCC) and their rules.
3. REXX APIs and RAVEN automation rules.
4. Z commands and TPFDF concepts.
5. Entry Control Block (ECB) processing.

Output format: Return ONLY a valid Python dictionary structure like this (do not use markdown formatting, just the python code):
KNOWLEDGE = {
    "conventions": ["rule 1", "rule 2"],
    "macros": {"MACRO_NAME": "description and usage"},
    "rexx_raven": ["rule 1", "rule 2"],
    "z_commands": ["cmd1", "cmd2"],
    "ecb_processing": ["concept 1", "concept 2"]
}
"""

# We will chunk the text to fit into context window
# Since the text might be huge, we just take the first 60000 chars as a sample for the LLM
chunk = all_text[:80000]

try:
    resp = requests.post("http://localhost:11434/api/generate", json={
        "model": "qwen2.5-coder",
        "prompt": PROMPT + "\n\nDOCUMENTATION:\n" + chunk,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 32000}
    }, timeout=180)
    
    if resp.status_code == 200:
        result_text = resp.json().get('response', '')
        # extract dictionary
        match = re.search(r'KNOWLEDGE\s*=\s*\{.*\}', result_text, re.DOTALL)
        if match:
            kb_str = match.group(0)
            with open("backend/llm/tpf_knowledge.py", "w", encoding="utf-8") as f:
                f.write(kb_str)
            print("Successfully extracted and saved tpf_knowledge.py")
        else:
            print("Could not parse KNOWLEDGE dict from LLM response. Saving raw response.")
            with open("backend/llm/tpf_knowledge.py", "w", encoding="utf-8") as f:
                f.write('KNOWLEDGE = {"raw": """' + result_text.replace('"', '\\"') + '"""}')
    else:
        print(f"Ollama error: {resp.text}")
except Exception as e:
    print(f"Error calling Ollama: {e}")
