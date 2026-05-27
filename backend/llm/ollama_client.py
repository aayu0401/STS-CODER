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
You are STS Coder, an expert IBM z/TPF RAVEN Automation Engineer, TPF Operations Server Specialist, and REXX developer.

## IBM z/TPF Domain Rules
- Programs are System/390 BAL (Basic Assembler Language) with IBM z/TPF macros.
- Key macros: ENTER/EXITC/EXITN/BACKC (lifecycle), FINDA/FILEC/FIWHC/UNFRC (file), GETCC/RELCC/GLOBZ (storage).
- EVERY FIWHC must have a matching UNFRC before EXITC/EXITN.
- EVERY GETCC must have a matching RELCC before EXITC/EXITN.
- ECB (Entry Control Block) is the core transaction context. CE1CR0 = input data.
- Programs MUST be strictly reentrant. No self-modifying code.
- REXX in z/TPF runs in RAVEN environment. First line: /* REXX */. Use ADDRESS RAVEN.

## TDRV File Format (RAVEN Standard)
* TDRV: <name>
* PURPOSE: <description>
* DATE: YYYY-MM-DD | AUTHOR: STS Coder AI
*--------------------------------------------------------------
* STEP 001: <description>
SEND "<z-command>"
WAIT 30
EXPECT "*COMMAND COMPLETE*" PASS
EXPECT "*ERROR*" FAIL
*--------------------------------------------------------------
* STEP 002: <description>
SEND "<next-command>"
WAIT 60
EXPECT "*SUCCESS*" PASS
EXPECT "*FAILED*" FAIL
RETRY 3
DELAY 10
*--------------------------------------------------------------
* RECOVERY SECTION
SEND "<recovery-command>"
WAIT 30
EXPECT "*RECOVERED*" PASS
*--------------------------------------------------------------
* END OF TDRV

Rules: Sequential SEND, WAIT for timeout, EXPECT with wildcards for PASS/FAIL, RETRY with DELAY.

## VAR File Format (Operations Server Standard)
VARIATION_DESCRIPTION = "<description>"
START_UP_TASKS:
  CMD "<startup-command>"
END
VARIATION_CMD:
  CMD "<monitoring-command>"
END
VARIATION:
  TRAP MSG="<pattern>" ACTION="<rexx-script-or-command>"
  TRAP MSG="<error-pattern>" ACTION="RECOVERY"
END
SHUTDOWN_TASKS:
  CMD "<cleanup-command>"
END

Also include fixed-width variable table:
VAR NAME         TYPE    LEN  SOURCE       DEFAULT     VALIDATION    DESCRIPTION

## REXX/RAVEN Template
/* REXX -- IBM z/TPF RAVEN Automation */
/* Purpose: <purpose> */
ADDRESS RAVEN
PARSE ARG input_parms
'<Z-command>'
IF RC \= 0 THEN CALL error_handler RC
PARSE VAR response field1 field2
EXIT 0
error_handler: PROCEDURE
  PARSE ARG rc_code
  SAY DATE('S') TIME() 'ERROR: RC='rc_code
RETURN

## TDR Document Sections
TDR NAME / ENTRY / SEGMENT / PURPOSE / INPUT FIELDS / OUTPUT FIELDS /
DEPENDENCIES / EXCEPTIONS (with RC codes) / Z COMMANDS / REXX INTERFACE /
RECOVERY FLOW / DEPLOYMENT INSTRUCTIONS / OPERATIONAL BEST PRACTICES

## Output Rules
- Respond ONLY with the artifact (VAR/TDRV/TDR/REXX). No prose wrapper.
- Use real IBM z/TPF macro names and Z-Commands only.
- Include standard variables: ERR_CODE, RET_CODE, ECB_PTR.
- Always include Z COMMANDS and RECOVERY sections in TDR.
- TDRV must use SEND/WAIT/EXPECT/RETRY/DELAY format.
- VAR must use VARIATION_DESCRIPTION/VARIATION_CMD/VARIATION/TRAP format.
- REXX must use ADDRESS RAVEN and proper RC checking.
"""

ADVISOR_SYSTEM = """\
You are STS Advisor, a senior IBM z/TPF RAVEN engineering consultant and automation auditor.
Produce a JSON array of engineering recommendations. Each item:
{"severity": "ERROR"|"WARNING"|"INFO"|"OPTIMIZATION", "category": string, "text": string, "code_hint": string|null}

## Automation Audit Rules
- FIWHC without UNFRC -> ERROR (file lock leak, ECB deadlock risk)
- GETCC without RELCC -> WARNING (storage leak, core block depletion)
- Missing error handling (no EXITN path) -> WARNING
- SEND without EXPECT -> WARNING (unvalidated command execution)
- Missing RETRY on critical commands -> WARNING
- No TIMEOUT/WAIT specified -> WARNING
- Missing recovery section in TDRV -> WARNING
- TRAP without error pattern -> INFO
- No REXX RC checking -> WARNING
- ECB safety and PNR access protection
- Z-Command monitoring coverage gaps
- Performance and storage efficiency
- Message trap completeness
- Recovery automation robustness
- Operations Server integration quality
- Self-healing capability gaps

## Categories
ERROR_HANDLING, EXIT_LOGIC, STORAGE, FILE_SAFETY, VALIDATION,
AUTOMATION, RECOVERY, MONITORING, REXX_QUALITY, PERFORMANCE,
SECURITY, OPERATIONS, DEPLOYMENT

Respond ONLY with valid JSON array. No prose, no markdown fences.
"""

CHAT_SYSTEM = """\
You are the STS Coder IBM z/TPF Copilot, a senior IBM z/TPF RAVEN Automation Engineer and System Specialist.
Your goal is to provide expert technical guidance on IBM z/TPF system architecture, RAVEN automation, REXX scripts, TDR documentation, VAR files, BAL assembler, and Z-Commands.

## Guidance Rules:
- Act as an elite z/TPF consultant. Be technically precise, helpful, and concise.
- Output clean, professional markdown formatting.
- Provide practical examples (REXX code blocks, Assembler snippets, or Z-Command examples) when relevant.
- Do NOT output JSON recommendations. Always answer in conversational prose or clear bullet points.
- If referencing a Z-Command, explain its syntax and function.
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
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            yield f"[Error: Model '{model}' not pulled. Run 'ollama pull {model}' in terminal to activate chat.]"
        else:
            yield f"[Error: Ollama HTTP {e.response.status_code}]"
    except httpx.RequestError as e:
        yield f"[Error: Ollama network request failed - {str(e)}]"
    except Exception as e:
        yield f"[Error: {str(e)}]"


def _macros_from_summary(parsed_summary: dict) -> list:
    """Macros list from parser summary (supports macros_called and macros keys)."""
    return parsed_summary.get("macros_called") or parsed_summary.get("macros") or []


def explain_z_command_stream(command: str):
    """Stream Z-Command explanation — knowledge base first, LLM for unknown commands."""
    from .tpf_knowledge import ZCMD_RESPONSES, format_zcmd_explanation, stream_text_chunks, parse_zcmd_verb

    base_cmd = parse_zcmd_verb(command)
    detail = ZCMD_RESPONSES.get(base_cmd)
    if detail:
        yield from stream_text_chunks(format_zcmd_explanation(command, detail))
        return

    prompt = (
        f"Explain the IBM z/TPF operator command: {command}\n"
        f"Format: **Command:** <name>\n**Purpose:** <purpose>\n"
        f"**Syntax:** <syntax>\n**Description:** <detail>\n"
        f"**Expected Response:** <typical console output>\n**Example:** <usage>"
    )
    yield from stream_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.1, num_predict=300)


def chat_stream(query: str):
    """Stream z/TPF copilot chat — KB-first (Z-commands, topics), LLM when needed."""
    from .tpf_knowledge import (
        KNOWLEDGE, ZCMD_RESPONSES, ZTPF_SYSTEM_KNOWLEDGE, CHAT_TOPICS,
        format_zcmd_explanation, stream_text_chunks, parse_zcmd_verb,
    )
    q_lower = query.lower().strip()

    # Z-command at start of query — instant KB when available
    first_word = parse_zcmd_verb(query)
    zcmd_detail = ZCMD_RESPONSES.get(first_word)
    if zcmd_detail:
        yield from stream_text_chunks(format_zcmd_explanation(query, zcmd_detail))
        return

    # Topic routing — stream KB text directly when Ollama offline; enrich when online
    matched_topic = None
    for keyword, topic in CHAT_TOPICS.items():
        if keyword in q_lower:
            matched_topic = topic
            break

    if matched_topic and matched_topic in ZTPF_SYSTEM_KNOWLEDGE:
        kb_text = ZTPF_SYSTEM_KNOWLEDGE[matched_topic].strip()
        if not is_ollama_available():
            yield from stream_text_chunks(kb_text[:3500])
            return
        prompt = (
            f"Using the following IBM z/TPF reference material, answer this question concisely:\n\n"
            f"Question: {query}\n\nReference Material:\n{kb_text}\n\n"
            f"Provide a clear, structured answer with examples where relevant."
        )
        yield from stream_ollama(
            ADVISOR_MODEL,
            CHAT_SYSTEM,
            prompt, temperature=0.3, num_predict=400,
        )
        return

    kb_entry = KNOWLEDGE.get("z_commands", {}).get(first_word, "")
    if kb_entry and not zcmd_detail:
        if not is_ollama_available():
            yield from stream_text_chunks(
                f"**Command:** {first_word}\n**Purpose:** {kb_entry}"
            )
            return
        prompt = (
            f"Explain the IBM z/TPF '{first_word}' operator command.\n"
            f"Definition: {kb_entry}\nGive operational guidance and when to use it."
        )
        yield from stream_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.2, num_predict=350)
        return

    # General z/TPF knowledge chat
    if not is_ollama_available():
        matches = []
        for cmd, purpose in KNOWLEDGE.get("z_commands", {}).items():
            if any(w in purpose.lower() for w in q_lower.split() if len(w) > 3):
                matches.append(f"  • **{cmd}**: {purpose[:80]}")
        if matches:
            yield from stream_text_chunks(
                "Relevant Z-Commands from knowledge base:\n\n" + "\n".join(matches[:6])
            )
        else:
            yield from stream_text_chunks(
                "Ollama is offline. Try a specific Z-Command (e.g. ZDSYS, ZDECB, ZOSRV) "
                "or ask about VAR, TDR, TDRV, REXX, or TOS automation."
            )
        return

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
    yield from stream_ollama(ADVISOR_MODEL, CHAT_SYSTEM, prompt, temperature=0.35, num_predict=450)


# ─────────────────────────────────────────────
# CODER FUNCTIONS (Qwen2.5-Coder)
# IBM REXX / RAVEN, VAR, TDRV, TDR
# ─────────────────────────────────────────────

def generate_var_llm(parsed_summary: dict) -> str:
    """Generate a production IBM z/TPF VAR file with proper fixed-width format."""
    entry = parsed_summary.get('entry_name', 'TRXXX')
    macros_found = _macros_from_summary(parsed_summary)

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
        f"Generate a complete IBM z/TPF Operations Server VAR file for entry {entry}.\n\n"
        f"Already defined variables (include in variable table):\n{static_var}\n\n"
        f"Entry Analysis:\n{json.dumps(parsed_summary, indent=2)}\n\n"
        f"Required RAVEN VAR format:\n"
        f"VARIATION_DESCRIPTION = \"{entry} - Automation monitoring and recovery\"\n"
        f"START_UP_TASKS:\n"
        f"  CMD \"ZPROG DISPLAY {entry}\"\n"
        f"  CMD \"ZSTAT ALL\"\n"
        f"END\n"
        f"VARIATION_CMD:\n"
        f"  CMD \"ZSTAT ALL\"\n"
        f"  CMD \"ZPROG DISPLAY {entry}\"\n"
        f"END\n"
        f"VARIATION:\n"
        f"  TRAP MSG=\"*{entry}*COMPLETE*\" ACTION=\"LOG_SUCCESS\"\n"
        f"  TRAP MSG=\"*ERROR*\" ACTION=\"RECOVERY\"\n"
        f"  TRAP MSG=\"*ABEND*\" ACTION=\"ALERT\"\n"
        f"END\n"
        f"SHUTDOWN_TASKS:\n"
        f"  CMD \"ZLOG CLOSE\"\n"
        f"END\n\n"
        f"Then include the variable definition table:\n"
        f"{static_var}\n\n"
        f"Rules:\n"
        f"- Include TRAP for success, error, and abend patterns\n"
        f"- Add entry-specific TRAP patterns based on macros used\n"
        f"- Include REXX script triggers where applicable\n"
        f"- Types: CHAR/BIN/PACK/HEX/ADDR/EQU\n"
        f"- Sources: INPUT/FILE/SYSTEM/INTERNAL/ECB/COMPUTED\n"
        f"Output ONLY the VAR file content."
    )
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.05)


def generate_tdrv_llm(parsed_summary: dict, var_output: Optional[str] = None) -> str:
    """Generate a full IBM z/TPF TDRV (Test Driver) file with fixed-width step format."""
    entry = parsed_summary.get('entry_name', 'TRXXX')
    macros = _macros_from_summary(parsed_summary)
    has_file = any(m in macros for m in ['FINDA','FILEC','FIWHC'])
    has_storage = 'GETCC' in macros

    prompt = f"""Generate a complete IBM z/TPF RAVEN TDRV (Test Driver) file for entry {entry}.

Entry Analysis:
{json.dumps(parsed_summary, indent=2)}

Required RAVEN TDRV format:
* TDRV: {entry}
* PURPOSE: Automation test driver for {entry}
* DATE: 2026-05-20 | AUTHOR: STS Coder AI
*--------------------------------------------------------------
* STEP 001: Entry initialization and system check
SEND "ZPROG DISPLAY {entry}"
WAIT 30
EXPECT "*LOADED*" PASS
EXPECT "*NOT FOUND*" FAIL
*--------------------------------------------------------------
* STEP 002: Input validation
SEND "ZSTAT ALL"
WAIT 30
EXPECT "*ACTIVE*" PASS
EXPECT "*ERROR*" FAIL
{'*--------------------------------------------------------------' + chr(10) + '* STEP 003: Storage verification' + chr(10) + 'SEND "ZPOOL DISPLAY"' + chr(10) + 'WAIT 30' + chr(10) + 'EXPECT "*AVAILABLE*" PASS' + chr(10) + 'EXPECT "*DEPLETED*" FAIL' + chr(10) + 'RETRY 3' + chr(10) + 'DELAY 5' if has_storage else ''}
{'*--------------------------------------------------------------' + chr(10) + '* STEP: File system access' + chr(10) + 'SEND "ZFILE STATUS"' + chr(10) + 'WAIT 60' + chr(10) + 'EXPECT "*OPEN*" PASS' + chr(10) + 'EXPECT "*CLOSED*" FAIL' + chr(10) + 'EXPECT "*LOCKED*" FAIL' + chr(10) + 'RETRY 2' + chr(10) + 'DELAY 10' if has_file else ''}

Add additional steps for:
- Data processing and transformation
- Output formatting and validation
- Error handling with recovery commands
- Final status check

Rules:
- Use SEND/WAIT/EXPECT/RETRY/DELAY format
- EXPECT patterns use wildcards (*) for matching
- Every SEND must have EXPECT PASS and EXPECT FAIL
- Include RETRY and DELAY for critical operations
- Include RECOVERY section at end
- Include * END OF TDRV marker
Output ONLY the TDRV file."""
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.05)


def generate_tdr_llm(parsed_summary: dict, var_output: Optional[str] = None,
                     tdrv_output: Optional[str] = None) -> str:
    """Generate a full IBM z/TPF TDR (Transaction Design Record) document."""
    entry = parsed_summary.get('entry_name', 'TRXXX')
    macros = _macros_from_summary(parsed_summary)
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
4. VERSION: 1.0 | DATE: 2026-05-20 | AUTHOR: STS Coder AI
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
13. RECOVERY FLOW:
    - Step-by-step recovery procedure for each failure mode
    - Recovery commands and expected results
    - Escalation path when recovery fails
14. DEPLOYMENT INSTRUCTIONS:
    - Pre-deployment checks
    - Deployment steps
    - Post-deployment validation
    - Rollback procedure
15. OPERATIONAL BEST PRACTICES:
    - Monitoring frequency recommendations
    - Alert thresholds
    - Log retention policy
    - Self-healing automation triggers

Output ONLY the TDR document."""
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.1)


def generate_rexx_llm(parsed_summary: dict) -> str:
    """Use Qwen2.5-Coder to generate IBM z/TPF REXX (RAVEN) automation exec."""
    entry = parsed_summary.get('entry_name', 'TRXXX')
    macros = _macros_from_summary(parsed_summary)
    purpose = parsed_summary.get('purpose', 'TPF automation')

    prompt = f"""Generate a production-ready IBM z/TPF REXX exec (RAVEN environment) for entry {entry}.

Entry Summary:
{json.dumps(parsed_summary, indent=2)}

Required REXX structure:
/* REXX -- IBM z/TPF RAVEN Automation: {entry} */
/* Purpose: {purpose} */
/* Generated by STS Coder AI */
ADDRESS RAVEN

PARSE ARG input_parms
max_retries = 3
delay_seconds = 5

/* Step 1: System verification */
'ZPROG DISPLAY {entry}'
IF RC \= 0 THEN DO
  CALL log_event 'ERROR', '{entry} not loaded RC='RC
  CALL error_handler RC
END

/* Step 2: Status check */
'ZSTAT ALL'
IF RC \= 0 THEN CALL log_event 'WARNING', 'ZSTAT RC='RC

/* Step 3: Command execution with retry */
DO retry_count = 1 TO max_retries
  '<primary-command>'
  IF RC = 0 THEN LEAVE
  CALL log_event 'WARNING', 'Retry' retry_count 'of' max_retries
  CALL SysSleep delay_seconds
END
IF RC \= 0 THEN DO
  CALL log_event 'ERROR', 'All retries exhausted'
  CALL error_handler RC
END

/* Response parsing */
PARSE VAR response status_field data_field

CALL log_event 'INFO', '{entry} automation completed successfully'
EXIT 0

log_event: PROCEDURE
  PARSE ARG level, message
  SAY DATE('S') TIME() level ':' message
RETURN

error_handler: PROCEDURE
  PARSE ARG rc_code
  SAY DATE('S') TIME() 'ALERT: Critical error RC='rc_code
  /* Recovery: attempt system reset */
  'ZSTAT ALL'
  EXIT rc_code
RETURN

The REXX must include:
- ADDRESS RAVEN environment
- PARSE ARG for input parameters
- Command execution with RC checking
- Retry logic with configurable count/delay
- Response parsing with PARSE VAR
- Structured logging via log_event subroutine
- Error handler with recovery attempt
- Proper EXIT codes
- Inline comments for each section
- Macros used in this entry: {', '.join(macros) if macros else 'NONE'}

Output ONLY the REXX source code.
"""
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.15)


def explain_z_command_llm(command: str) -> str:
    """Explain a ZTPF Z Command — rich KB first, LLM only for unknown commands."""
    from .tpf_knowledge import ZCMD_RESPONSES, format_zcmd_explanation, parse_zcmd_verb

    base_cmd = parse_zcmd_verb(command)
    detail = ZCMD_RESPONSES.get(base_cmd)
    if detail:
        return format_zcmd_explanation(command, detail)

    prompt = f"""Explain this IBM z/TPF Z Command.
Command: {command}

Provide purpose, syntax, expected console response, return codes, and example usage.
Format:
**Command:** <name>
**Purpose:** <purpose>
**Syntax:** <syntax>
**Expected Response:** <typical output>
**Details:** <explanation>
"""
    return _call_ollama(CODER_MODEL, CODER_SYSTEM, prompt, temperature=0.1, num_predict=FAST_TOKENS)


def generate_rexx_static(parsed_summary: dict) -> str:
    """Static REXX/RAVEN template when Ollama is unavailable."""
    entry = parsed_summary.get("entry_name", "TRXXX")
    macros = ", ".join(_macros_from_summary(parsed_summary)) or "NONE"
    purpose = parsed_summary.get("purpose", "TPF transaction monitoring")
    return f"""/* REXX — IBM z/TPF RAVEN Exec: {entry} */
/* Purpose: {purpose} */
/* Macros in entry: {macros} */

ADDRESS RAVEN

PARSE ARG entry_input

IF entry_input = '' THEN DO
  SAY 'ERR: No input provided'
  EXIT 8
END

/* TOS automation: verify Operations Server connectivity */
'ZOSRV DISPLAY'
IF RC \\= 0 THEN DO
  SAY 'WARNING: ZOSRV RC='RC
END

'ZPROG DISPLAY {entry}'
IF RC = 0 THEN
  SAY '{entry} is LOADED'
ELSE DO
  SAY 'ALERT: {entry} NOT LOADED — RC='RC
  EXIT 4
END

'ZSTAT ALL'
IF RC \\= 0 THEN SAY 'WARNING: ZSTAT RC='RC

SAY 'OK: {entry} monitoring complete'
EXIT 0
"""


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
    Phase 1 (Qwen2.5-Coder): Analyze -> VAR -> TDR -> REXX
    Phase 2 (Llama 3.3):     Recommendations using ALL Phase 1 outputs
    Phase 3 (Feedback):      Return combined result with cross-model context

    Returns dict with: analysis, var_file, tdr_file, rexx_exec, recommendations
    """
    result = {
        "llm_mode": "dual_model_reinforcement",
        "coder_model": CODER_MODEL,
        "advisor_model": ADVISOR_MODEL,
        "analysis": {},
        "var_file": "",
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

    with ThreadPoolExecutor(max_workers=4) as executor:
        f_analysis = executor.submit(safe_run, analyze_entry_llm, raw_text, parsed_summary)
        f_var      = executor.submit(safe_run, generate_var_llm, parsed_summary)
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
        log.info(f"[LLM] Phase 2: {ADVISOR_MODEL} -- recommendations")
        result["recommendations"] = generate_recommendations_llm(
            parsed_summary,
            var_output=result["var_file"] or None,
            tdrv_output=None,
            TDR_output=result["tdr_file"] or None,
            coder_analysis=result["analysis"] or None,
        )
    except Exception as e:
        result["errors"].append(f"Llama recommendations: {e}")
        result["recommendations"] = _fallback_recommendations(parsed_summary)

    return result
