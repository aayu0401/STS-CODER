"""
STS Coder — Ollama Dual-Model LLM Client
==========================================
Qwen2.5-Coder  → IBM REXX / Raven coding, VAR / TDRV / TDR generation
Llama 3.3      → Engineering recommendations & risk narrative
Reinforcement  → Models share context / feedback for collaborative refinement

Both models are invoked via the local Ollama REST API (http://localhost:11434).
"""

import re
import json
import logging
import httpx
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from .tpf_knowledge import KNOWLEDGE

log = logging.getLogger("sts.llm")

OLLAMA_BASE   = "http://localhost:11434"
CODER_MODEL   = "qwen2.5-coder:1.5b"   # IBM REXX / VAR / TDRV / TDR
ADVISOR_MODEL = "llama3.2"              # Recommendations / risk narrative

TIMEOUT       = 150   # seconds per request
FAST_TOKENS   = 256   # Z-CMD / Chat  — short, precise
FULL_TOKENS   = 768   # VAR / TDRV / TDR / REXX — structured docs
ANALYSIS_TOKENS = 256 # JSON analysis

# ─────────────────────────────────────────────
# Z/TPF ZTPF SYSTEM PROMPT — Qwen2.5-Coder
# Trained on Z Command Entries and ZTPF patterns
# ─────────────────────────────────────────────

CODER_SYSTEM = """\
You are STS Coder, an expert IBM z/TPF system programmer and REXX/RAVEN specialist.

## IBM z/TPF Domain Rules
- Programs are System/390 BAL (Basic Assembler Language) with IBM z/TPF macros.
- Key macros: ENTER/EXITC/EXITN/BACKC (lifecycle), FINDA/FILEC/FIWHC/UNFRC (file), GETCC/RELCC/GLOBZ (storage).
- EVERY FIWHC must have a matching UNFRC before EXITC/EXITN.
- EVERY GETCC must have a matching RELCC before EXITC/EXITN.
- ECB (Entry Control Block) is the core transaction context. CE1CR0 = input data.
- Programs MUST be strictly reentrant. No self-modifying code.
- REXX in z/TPF runs in RAVEN environment. First line: /* REXX */. Use ADDRESS RAVEN.

## VAR File — Fixed-width columns
VAR NAME         TYPE    LEN  SOURCE       DEFAULT     VALIDATION    DESCRIPTION
ERR_CODE         BIN     2    INTERNAL     X'0000'     0000-9999     Error return code
INPUT_KEY        CHAR    8    CE1CR0+0     SPACES      NON-BLANK     Primary key input
FILE_PTR         ADDR    4    FILE         N/A         NON-NULL      Record pointer

Types: CHAR/BIN/PACK/HEX/ADDR/EQU
Sources: INPUT/FILE/SYSTEM/INTERNAL/ECB/COMPUTED

## TDRV File — Fixed-width columns
STEP  ACTION                    ENTRY      CONDITION              NEXT
001   RECEIVE REQUEST           TRXXX      ECB dispatched         002
002   VALIDATE INPUT            TRXXX      CE1CR0 non-blank       003 / ERR-001
003   ALLOCATE STORAGE          TRXXX      GETCC success          004 / ERR-002
004   FILE ACCESS - READ        TRXXX      FINDA success          005 / ERR-003
005   PROCESS DATA              TRXXX      Record valid           006
006   FORMAT OUTPUT             TRXXX      Data formatted         007
007   RETURN RESPONSE           TRXXX      RC=0                   EXIT
ERR-001 ERROR HANDLING          TRXXX      Invalid input RC=16    EXIT-ERR
EXIT    EXITC                   TRXXX      Normal end             -
EXIT-ERR EXITN                  TRXXX      Error end              -

## TDR Document Sections
TDR NAME / ENTRY / SEGMENT / PURPOSE / INPUT FIELDS / OUTPUT FIELDS /
DEPENDENCIES / EXCEPTIONS (with RC codes) / Z COMMANDS / REXX INTERFACE

## REXX/RAVEN Template
/* REXX */
ADDRESS RAVEN
PARSE ARG entry_name
'ZSTAT ALL'
IF RC \= 0 THEN SAY 'WARNING: ZSTAT RC='RC
'ZPROG DISPLAY' entry_name
IF RC = 0 THEN SAY entry_name 'is LOADED'
EXIT 0

## Output Rules
- Respond ONLY with the artifact (VAR/TDRV/TDR/REXX). No prose wrapper.
- Use real IBM z/TPF macro names only.
- Include all standard variables: ERR_CODE, RET_CODE, ECB_PTR.
- Always include Z COMMANDS section in TDR.
"""

ADVISOR_SYSTEM = """\
You are STS Advisor, a senior IBM z/TPF engineering consultant.
Produce a JSON array of engineering recommendations. Each item:
{"severity": "ERROR"|"WARNING"|"INFO"|"OPTIMIZATION", "category": string, "text": string, "code_hint": string|null}

Focus on:
- FIWHC without UNFRC → ERROR
- GETCC without RELCC → WARNING  
- Missing error handling (no EXITN path) → WARNING
- ECB safety and PNR access protection
- REXX quality and RC checking
- Z-Command monitoring coverage
- Performance and storage efficiency

Respond ONLY with valid JSON array. No prose, no markdown fences.
"""


# ─────────────────────────────────────────────
# LOW-LEVEL OLLAMA CALL
# ─────────────────────────────────────────────

def _call_ollama(model: str, system: str, user_prompt: str, temperature: float = 0.2, num_predict: int = FULL_TOKENS) -> str:
    """
    Call the Ollama /api/generate endpoint.
    Returns the assembled response string.
    """
    payload = {
        "model": model,
        "system": system,
        "prompt": user_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": num_predict,
            "stop": [],
        },
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except httpx.ConnectError:
        raise ConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_BASE}. "
            "Ensure Ollama is running: `ollama serve`"
        )


def is_ollama_available() -> bool:
    """Quick health check — returns True if Ollama is reachable."""
    try:
        with httpx.Client(timeout=5) as client:
            r = client.get(f"{OLLAMA_BASE}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


def list_available_models() -> list[str]:
    """Return list of locally available Ollama model names."""
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(f"{OLLAMA_BASE}/api/tags")
            r.raise_for_status()
            tags = r.json().get("models", [])
            return [t["name"] for t in tags]
    except Exception:
        return []



# ─────────────────────────────────────────────
# STREAMING OLLAMA CALL
# ─────────────────────────────────────────────

def stream_ollama(model: str, system: str, user_prompt: str, temperature: float = 0.2, num_predict: int = FAST_TOKENS):
    """
    Stream tokens from Ollama one chunk at a time.
    Yields raw token strings immediately as generated.
    """
    payload = {
        "model": model,
        "system": system,
        "prompt": user_prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": num_predict,
        },
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            with client.stream("POST", f"{OLLAMA_BASE}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
    except httpx.ConnectError:
        yield "[Error: Ollama not reachable]"


def explain_z_command_stream(command: str):
    """Stream a rich, detailed Z-Command explanation token by token."""
    from .tpf_knowledge import KNOWLEDGE, ZCMD_RESPONSES
    base_cmd = command.strip().split()[0].upper() if command.strip() else ""
    detail    = ZCMD_RESPONSES.get(base_cmd)
    kb_entry  = KNOWLEDGE.get("z_commands", {}).get(base_cmd, "")

    if detail:
        prompt = (
            f"Explain the IBM z/TPF '{base_cmd}' operator command in detail.\n\n"
            f"Purpose: {detail['purpose']}\n"
            f"Syntax: {detail['syntax']}\n"
            f"Description: {detail['description']}\n"
            f"Category: {detail['category']}\n\n"
            f"Format your response as:\n"
            f"**Command:** {base_cmd}\n"
            f"**Purpose:** <1 sentence>\n"
            f"**Syntax:** <syntax>\n"
            f"**Description:** <2-3 sentences of detail>\n"
            f"**Output Fields:** <key fields shown>\n"
            f"**Example:** <example usage>\n"
            f"**When to Use:** <operational guidance>"
        )
    else:
        prompt = (
            f"Explain the IBM z/TPF operator command: {command}\n"
            f"Format: **Command:** <name>\n**Purpose:** <purpose>\n"
            f"**Syntax:** <syntax>\n**Description:** <detail>\n**Example:** <usage>"
        )
    yield from stream_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.1, num_predict=300)


def chat_stream(query: str):
    """Stream a rich z/TPF copilot chat response with KB-first routing."""
    from .tpf_knowledge import KNOWLEDGE, ZTPF_SYSTEM_KNOWLEDGE, CHAT_TOPICS
    q_lower = query.lower().strip()

    # Try topic routing first — return instant KB answer
    matched_topic = None
    for keyword, topic in CHAT_TOPICS.items():
        if keyword in q_lower:
            matched_topic = topic
            break

    if matched_topic and matched_topic in ZTPF_SYSTEM_KNOWLEDGE:
        kb_text = ZTPF_SYSTEM_KNOWLEDGE[matched_topic].strip()
        prompt = (
            f"Using the following IBM z/TPF reference material, answer this question concisely and accurately:\n\n"
            f"Question: {query}\n\n"
            f"Reference Material:\n{kb_text}\n\n"
            f"Provide a clear, structured answer with examples where relevant."
        )
        yield from stream_ollama(ADVISOR_MODEL, ADVISOR_SYSTEM.replace('Produce a JSON array', 'Answer helpfully as a senior z/TPF expert. Do NOT produce JSON.'), prompt, temperature=0.3, num_predict=400)
        return

    # Check Z-command in query
    first_word = query.strip().split()[0].upper()
    kb_entry = KNOWLEDGE.get("z_commands", {}).get(first_word, "")
    if kb_entry:
        prompt = (
            f"Explain the IBM z/TPF '{first_word}' operator command.\n"
            f"Definition: {kb_entry}\n"
            f"Give operational guidance and when to use it."
        )
        yield from stream_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.2, num_predict=350)
        return

    # General z/TPF knowledge chat
    system_ctx = "\n".join(KNOWLEDGE.get("conventions", [])[:3])
    prompt = (
        f"You are the STS Coder IBM z/TPF Copilot — a senior z/TPF expert.\n"
        f"Answer the following question with IBM z/TPF expertise:\n\n"
        f"Question: {query}\n\n"
        f"Core z/TPF Principles:\n{system_ctx}\n\n"
        f"Provide a detailed, technically accurate answer covering:\n"
        f"- What it is / how it works in z/TPF\n"
        f"- Relevant macros or Z-Commands\n"
        f"- Best practices and common pitfalls\n"
        f"- Example code or command if applicable"
    )
    yield from stream_ollama(ADVISOR_MODEL, ADVISOR_SYSTEM.replace('Produce a JSON array', 'Answer helpfully as a senior z/TPF expert. Do NOT produce JSON.'), prompt, temperature=0.35, num_predict=450)


# ─────────────────────────────────────────────
# CODER FUNCTIONS (Qwen2.5-Coder)
# IBM REXX / RAVEN, VAR, TDRV, TDR
# ─────────────────────────────────────────────

def generate_var_llm(parsed_summary: dict) -> str:
    """Generate a production IBM z/TPF VAR file with proper fixed-width format."""
    entry = parsed_summary.get('entry_name', 'TRXXX')
    macros_found = parsed_summary.get('macros', [])

    # Pre-define strings that contain quotes (avoids backslash in f-string)
    x0000  = "X'0000'"
    x00    = "X'00'"
    x00ff  = "X'00'-X'FF'"
    na     = "N/A"
    ge0    = ">=0"

    var_lines = [
        f"{'VAR NAME':<20} {'TYPE':<6} {'LEN':<5} {'SOURCE':<12} {'DEFAULT':<12} {'VALIDATION':<16} DESCRIPTION",
        "=" * 100,
        f"{'ERR_CODE':<20} {'BIN':<6} {'2':<5} {'INTERNAL':<12} {x0000:<12} {'0000-9999':<16} Error return code",
        f"{'RET_CODE':<20} {'BIN':<6} {'2':<5} {'INTERNAL':<12} {x0000:<12} {'0000-9999':<16} Function return code",
        f"{'ECB_PTR':<20} {'ADDR':<6} {'4':<5} {'ECB':<12} {na:<12} {'NON-NULL':<16} ECB base address pointer",
        f"{'INPUT_KEY':<20} {'CHAR':<6} {'8':<5} {'CE1CR0+0':<12} {'SPACES':<12} {'NON-BLANK':<16} Primary input key from request",
    ]
    if 'FINDA' in macros_found or 'FILEC' in macros_found:
        var_lines.append(f"{'FILE_REC_PTR':<20} {'ADDR':<6} {'4':<5} {'FILE':<12} {na:<12} {na:<16} Pointer to retrieved file record")
        var_lines.append(f"{'FILE_STATUS':<20} {'BIN':<6} {'2':<5} {'SYSTEM':<12} {x0000:<12} {'0-FF':<16} File operation return status")
    if 'GETCC' in macros_found:
        var_lines.append(f"{'WORK_AREA_PTR':<20} {'ADDR':<6} {'4':<5} {'INTERNAL':<12} {na:<12} {'NON-NULL':<16} Working storage area pointer")
    var_lines.extend([
        f"{'PROCESS_FLAG':<20} {'BIN':<6} {'1':<5} {'INTERNAL':<12} {x00:<12} {x00ff:<16} Processing control flags",
        f"{'OUTPUT_LEN':<20} {'BIN':<6} {'4':<5} {'COMPUTED':<12} {'0':<12} {ge0:<16} Length of output response",
        "",
        f"ENTRY: {entry}    GENERATED BY: STS Coder AI    DATE: 2026-05-13",
    ])
    static_var = "\n".join(var_lines)

    prompt = (
        f"Generate a complete IBM z/TPF VAR (Variable Definition) file for entry {entry}.\n\n"
        f"Already defined variables (add more based on this entry's logic):\n{static_var}\n\n"
        f"Entry Analysis:\n{json.dumps(parsed_summary, indent=2)}\n\n"
        f"Rules:\n"
        f"- Use fixed-width column format exactly as shown above\n"
        f"- Add entry-specific variables beyond the standards above\n"
        f"- Types: CHAR/BIN/PACK/HEX/ADDR/EQU\n"
        f"- Sources: INPUT/FILE/SYSTEM/INTERNAL/ECB/COMPUTED\n"
        f"- Include ALL variables referenced by macros in the code\n"
        f"Output ONLY the VAR file content."
    )
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.05)


def generate_tdrv_llm(parsed_summary: dict, var_output: Optional[str] = None) -> str:
    """Generate a full IBM z/TPF TDRV (Test Driver) file with fixed-width step format."""
    entry = parsed_summary.get('entry_name', 'TRXXX')
    macros = parsed_summary.get('macros', [])
    has_file = any(m in macros for m in ['FINDA','FILEC','FIWHC'])
    has_storage = 'GETCC' in macros

    prompt = f"""Generate a complete IBM z/TPF TDRV (Test Driver) file for entry {entry}.

Entry Analysis:
{json.dumps(parsed_summary, indent=2)}

Required TDRV fixed-width column format:
STEP  ACTION                    ENTRY      CONDITION              NEXT
001   RECEIVE REQUEST           {entry}    ECB dispatched         002
002   VALIDATE INPUT            {entry}    CE1CR0 non-blank       003 / ERR-001
{'003   ALLOCATE STORAGE          ' + entry + '    GETCC success          004 / ERR-002' if has_storage else ''}
{'00X   FILE ACCESS - READ        ' + entry + '    FINDA success          00Y / ERR-003' if has_file else ''}
XXX   PROCESS DATA              {entry}    Record valid           YYY
YYY   FORMAT OUTPUT             {entry}    Data formatted         ZZZ
ZZZ   RETURN RESPONSE           {entry}    RC=0                   EXIT
ERR-001 ERROR HANDLING          {entry}    Invalid input RC=16    EXIT-ERR
EXIT    EXITC                   {entry}    Normal end             -
EXIT-ERR EXITN                  {entry}    Error end              -

Rules:
- Every macro call must have an error path (ERR-XXX steps)
- Include FIWHC → UNFRC steps if file locking is detected
- Steps must be sequential with proper NEXT references
- Include ALL error conditions with specific RC codes
Output ONLY the TDRV file."""
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.05)


def generate_tdr_llm(parsed_summary: dict, var_output: Optional[str] = None,
                     tdrv_output: Optional[str] = None) -> str:
    """Generate a full IBM z/TPF TDR (Transaction Design Record) document."""
    entry = parsed_summary.get('entry_name', 'TRXXX')
    macros = parsed_summary.get('macros', [])
    z_cmds = []
    if any(m in macros for m in ['FINDA','FILEC','FIWHC']):
        z_cmds += ['ZTPFDF - Check database status', 'ZFILE  - Check file system status']
    if 'GETCC' in macros:
        z_cmds += ['ZPOOL  - Monitor core block depletion', 'ZSTAT  - Check ECB utilization']
    z_cmds += ['ZDECB  - Dump ECB after failure', 'ZTRAP  - Set debug trap on entry',
               'ZDUMP  - Full memory dump for post-mortem', 'ZECB   - Display active ECBs',
               'ZPROG  - Check program load status', 'ZLOG   - Monitor error messages']

    prompt = f"""Generate a complete IBM z/TPF TDR (Transaction Design Record) for entry {entry}.

Entry Analysis:
{json.dumps(parsed_summary, indent=2)}

Required sections:
1. TDR NAME: {entry}-TDR
2. ENTRY NAME: {entry}
3. SEGMENT: 00
4. VERSION: 1.0 | DATE: 2026-05-13 | AUTHOR: STS Coder AI
5. PURPOSE: Narrative description of what this entry does
6. INPUT FIELDS: Table of CE1CR0 offsets with field names, types, lengths, descriptions
7. OUTPUT FIELDS: Response fields with offsets, types, lengths
8. DEPENDENCIES: List ALL macros used and file systems accessed
9. EXCEPTIONS: ALL error conditions with RC codes and causes
   RC=0:  Success
   RC=4:  Record not found
   RC=8:  File system error
   RC=12: Storage allocation failure
   RC=16: Invalid input
10. DOWNSTREAM IMPACT: What systems/entries depend on this
11. Z COMMANDS FOR MONITORING AND DEBUGGING:
{chr(10).join('    ' + c for c in z_cmds)}
12. REXX/RAVEN INTERFACE: Sample RAVEN exec to monitor this entry

Output ONLY the TDR document."""
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.1)


def generate_rexx_llm(parsed_summary: dict) -> str:
    """Use Qwen2.5-Coder to generate IBM z/TPF REXX (RAVEN) exec."""
    prompt = f"""Generate an IBM z/TPF REXX exec (RAVEN environment) for this entry.

Entry Summary:
{json.dumps(parsed_summary, indent=2)}

The REXX exec should:
- Use proper RAVEN ADDRESS environment
- Handle ECB context
- Implement the entry's core logic in REXX
- Include Z Command integration where applicable
- Include error handling with REXX signal/procedure

Produce ONLY the REXX source code with inline comments.
"""
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.2)


def explain_z_command_llm(command: str) -> str:
    """Use Qwen2.5-Coder to explain a single ZTPF Z Command using the Knowledge Base."""
    # Extract base command verb (e.g. ZPAGE from ZPAGE F)
    base_cmd = command.strip().split()[0].upper()
    
    exact_purpose = KNOWLEDGE["z_commands"].get(base_cmd)
    
    if exact_purpose:
        prompt = f"""Explain the IBM z/TPF '{base_cmd}' command.

Here is the exact authoritative definition and purpose from the training data:
{exact_purpose}

Task:
Produce a precise response for the user containing the command and its purpose, expanding slightly on its use case based on the provided definition. 
Keep it clear and precise. Do not invent details outside of this definition.
Format it as:
**Command:** {base_cmd}
**Purpose:** <extracted purpose>
**Details:** <short expansion>
"""
    else:
        prompt = f"""Explain this IBM z/TPF Z Command.
Command: {command}

Provide a clear, precise explanation of what this command does, its purpose, and any important parameters.
Format it as:
**Command:** <Command Name>
**Purpose:** <Purpose>
**Details:** <short explanation>
"""
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.1, num_predict=FAST_TOKENS)


def analyze_entry_llm(raw_text: str, parsed_summary: dict) -> dict:
    """Use Qwen2.5-Coder to produce a structured analysis of the entry."""
    prompt = f"""Analyze this IBM z/TPF entry and produce a JSON analysis object.

Raw Entry Text:
{raw_text[:2000]}

Parsed Summary (from static analysis):
{json.dumps(parsed_summary, indent=2)}

Return a JSON object with these keys:
{{
  "entry_type": string,
  "purpose": string,
  "complexity": "LOW"|"MODERATE"|"HIGH"|"VERY HIGH",
  "z_commands_applicable": [list of relevant Z commands],
  "rexx_integration": boolean,
  "critical_paths": [list of critical execution paths],
  "ztpf_macros_identified": [list],
  "risk_factors": [list of strings]
}}

Respond ONLY with valid JSON.
"""
    try:
        raw = _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.1, num_predict=ANALYSIS_TOKENS)
        # Extract JSON
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {}
    except Exception as e:
        log.warning(f"LLM analysis parse failed: {e}")
        return {}


# ─────────────────────────────────────────────
# ADVISOR FUNCTIONS (Llama 3.3)
# Engineering Recommendations
# ─────────────────────────────────────────────

def generate_recommendations_llm(
    parsed_summary: dict,
    var_output: Optional[str] = None,
    tdrv_output: Optional[str] = None,
    TDR_output: Optional[str] = None,
    coder_analysis: Optional[dict] = None,
) -> list[dict]:
    """
    Use Llama 3.3 to generate engineering recommendations.
    Receives context from Qwen2.5-Coder outputs (reinforcement loop).
    """
    context_parts = [f"Entry Analysis:\n{json.dumps(parsed_summary, indent=2)}"]

    if coder_analysis:
        context_parts.append(f"\nQwen2.5-Coder Analysis:\n{json.dumps(coder_analysis, indent=2)}")

    if var_output:
        context_parts.append(f"\nGenerated VAR File (excerpt):\n{var_output[:500]}")

    if tdrv_output:
        context_parts.append(f"\nGenerated TDRV File (excerpt):\n{tdrv_output[:500]}")

    if TDR_output:
        context_parts.append(f"\nGenerated TDR File (excerpt):\n{TDR_output[:500]}")

    user_prompt = "\n".join(context_parts) + "\n\nProduce engineering recommendations as JSON array."

    try:
        raw = _call_ollama(ADVISOR_MODEL, ADVISOR_SYSTEM, user_prompt, temperature=0.3, num_predict=FAST_TOKENS)
        # Extract JSON array
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            recs = json.loads(m.group())
            if isinstance(recs, list):
                return recs
        return _fallback_recommendations(parsed_summary)
    except Exception as e:
        log.warning(f"Llama 3.3 recommendations parse failed: {e}")
        return _fallback_recommendations(parsed_summary)


def _fallback_recommendations(parsed_summary: dict) -> list[dict]:
    """Static fallback recommendations when Llama 3.3 is unavailable."""
    recs = []
    stats = parsed_summary.get("statistics", {})

    if not stats.get("error_points", 0):
        recs.append({
            "severity": "WARNING", "category": "ERROR_HANDLING",
            "text": "No explicit error handling detected. Add structured ERR label paths.",
            "code_hint": None
        })
    if not stats.get("macros", 0):
        recs.append({
            "severity": "WARNING", "category": "EXIT_LOGIC",
            "text": "No TPF macros detected. Verify ENTER/EXITC/BACKC lifecycle is correct.",
            "code_hint": "ENTER TDRR\n...\nEXITC TDRR"
        })
    recs.append({
        "severity": "INFO", "category": "VALIDATION",
        "text": "Validate all generated artifacts against live z/TPF system before production deployment.",
        "code_hint": None
    })
    return recs


# ─────────────────────────────────────────────
# REINFORCEMENT: FULL PIPELINE WITH FEEDBACK
# ─────────────────────────────────────────────

def run_full_pipeline_llm(raw_text: str, parsed_summary: dict) -> dict:
    """
    Reinforcement pipeline:
    Phase 1 (Qwen2.5-Coder): Analyze → VAR → TDRV → TDR → REXX
    Phase 2 (Llama 3.3):     Recommendations using ALL Phase 1 outputs
    Phase 3 (Feedback):      Return combined result with cross-model context

    Returns dict with: analysis, var_file, tdrv_file, tdr_file, rexx_exec, recommendations
    """
    result = {
        "llm_mode": "dual_model_reinforcement",
        "coder_model": CODER_MODEL,
        "advisor_model": ADVISOR_MODEL,
        "analysis": {},
        "var_file": "",
        "tdrv_file": "",
        "tdr_file": "",
        "rexx_exec": "",
        "recommendations": [],
        "errors": [],
    }

    # Phase 1: Run all Coder generation tasks in parallel
    log.info(f"[LLM] Phase 1: Running {CODER_MODEL} generations in parallel...")
    
    def safe_run(func, *args):
        try:
            return func(*args)
        except Exception as e:
            return e

    with ThreadPoolExecutor(max_workers=5) as executor:
        f_analysis = executor.submit(safe_run, analyze_entry_llm, raw_text, parsed_summary)
        f_var      = executor.submit(safe_run, generate_var_llm, parsed_summary)
        f_tdrv     = executor.submit(safe_run, generate_tdrv_llm, parsed_summary, None)
        f_tdr      = executor.submit(safe_run, generate_tdr_llm, parsed_summary, None, None)
        f_rexx     = executor.submit(safe_run, generate_rexx_llm, parsed_summary)
        
        res_analysis = f_analysis.result()
        if isinstance(res_analysis, Exception):
            result["errors"].append(f"Coder analysis: {res_analysis}")
        else:
            result["analysis"] = res_analysis
            
        res_var = f_var.result()
        if isinstance(res_var, Exception):
            result["errors"].append(f"VAR generation: {res_var}")
        else:
            result["var_file"] = res_var
            
        res_tdrv = f_tdrv.result()
        if isinstance(res_tdrv, Exception):
            result["errors"].append(f"TDRV generation: {res_tdrv}")
        else:
            result["tdrv_file"] = res_tdrv
            
        res_tdr = f_tdr.result()
        if isinstance(res_tdr, Exception):
            result["errors"].append(f"TDR generation: {res_tdr}")
        else:
            result["tdr_file"] = res_tdr
            
        res_rexx = f_rexx.result()
        if isinstance(res_rexx, Exception):
            result["errors"].append(f"REXX generation: {res_rexx}")
        else:
            result["rexx_exec"] = res_rexx

    # Phase 2: Llama 3.3 — recommendations with full Phase 1 context
    try:
        log.info(f"[LLM] Phase 2: {ADVISOR_MODEL} — recommendations")
        result["recommendations"] = generate_recommendations_llm(
            parsed_summary,
            var_output=result["var_file"] or None,
            tdrv_output=result["tdrv_file"] or None,
            TDR_output=result["tdr_file"] or None,
            coder_analysis=result["analysis"] or None,
        )
    except Exception as e:
        result["errors"].append(f"Llama recommendations: {e}")
        result["recommendations"] = _fallback_recommendations(parsed_summary)

    return result
