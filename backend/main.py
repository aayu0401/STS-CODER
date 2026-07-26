"""
STS Coder — FastAPI Backend Server  (v2.0 — Dual-Model LLM)
=============================================================
Travelport Smart TPF System Coder API

Models:
  Qwen2.5-Coder  → IBM REXX, VAR, TDR generation (ZTPF Z Command trained)
  Llama 3.3      → Engineering recommendations & risk narrative
  Reinforcement  → Coder outputs feed Advisor for cross-model refinement

Endpoints:
  POST /api/analyze            — Analyze TPF entry (static + LLM)
  POST /api/generate/var       — Generate VAR file (LLM-powered)
  POST /api/generate/tdr       — Generate TDR file (LLM-powered)
  POST /api/generate/rexx      — Generate REXX/RAVEN exec (LLM-powered)
  POST /api/generate/full      — Full engineering pack (dual-model reinforcement)
  POST /api/predict            — ML-based entry classification
  POST /api/train              — Trigger scikit-learn model training
  GET  /api/health             — Health check (includes Ollama status)
  GET  /api/models             — List available Ollama models

Run:
  cd backend
  uvicorn main:app --host 0.0.0.0 --port 8100 --reload
"""

import os
import sys
import json
import traceback
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sts.main")

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(__file__))

from parser.tpf_parser import parse_tpf_entry
from generators.var_generator import generate_var_file

from generators.tdr_generator import generate_tdr_file
from analyzer.entry_analyzer import generate_analysis, generate_recommendations
from llm import (
    is_ollama_available,
    list_available_models,
    run_full_pipeline_llm,
    generate_var_llm,

    generate_tdr_llm,
    generate_rexx_llm,
    generate_recommendations_llm,
    analyze_entry_llm,
    explain_z_command_llm,
    explain_z_command_stream,
    chat_stream,
    generate_rexx_static,
    CODER_MODEL,
    ADVISOR_MODEL,
)


# ═══════════════════════════════════════════
# APP INITIALIZATION
# ═══════════════════════════════════════════

app = FastAPI(
    title="STS Coder API",
    description=(
        "Travelport Smart TPF System Coder — IBM z/TPF Engineering Copilot.\n\n"
        "**Qwen2.5-Coder** handles IBM REXX, VAR, TDR generation.\n"
        "**Llama 3.3** provides engineering recommendations.\n"
        "Reinforcement feedback loop: coder outputs inform advisor analysis."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import hashlib
from threading import Lock

# ═══════════════════════════════════════════
# IN-MEMORY CACHE FOR LATENCY REDUCTION
# ═══════════════════════════════════════════
class ResponseCache:
    def __init__(self):
        self._cache = {}
        self._lock = Lock()

    def get(self, raw_text: str, endpoint: str, mode: str, use_llm: bool):
        sanitized = raw_text.strip()
        key = (hashlib.sha256(sanitized.encode("utf-8")).hexdigest(), endpoint, mode, use_llm)
        with self._lock:
            val = self._cache.get(key)
            if val is not None:
                log.info(f"[CACHE DEBUG GET] HIT for key {key}")
            else:
                log.info(f"[CACHE DEBUG GET] MISS for key {key}. Cache keys currently: {list(self._cache.keys())}")
            return val

    def set(self, raw_text: str, endpoint: str, mode: str, use_llm: bool, value):
        sanitized = raw_text.strip()
        key = (hashlib.sha256(sanitized.encode("utf-8")).hexdigest(), endpoint, mode, use_llm)
        with self._lock:
            if len(self._cache) >= 100:
                oldest = next(iter(self._cache))
                self._cache.pop(oldest, None)
            self._cache[key] = value
            log.info(f"[CACHE DEBUG SET] Stored key {key}")

    def clear(self):
        with self._lock:
            self._cache.clear()

GLOBAL_CACHE = ResponseCache()


# ═══════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════

class TPFEntryRequest(BaseModel):
    raw_text: str = Field(..., min_length=1, description="Raw TPF assembly / REXX / description text")
    entry_name: str = Field("", description="Optional entry name override")
    segment: str = Field("", description="Optional segment name")
    mode: str = Field("FULL", description="Output mode: ANALYZE, VAR, TDR, REXX, FULL")
    use_llm: bool = Field(True, description="Use Ollama LLM (falls back to static if unavailable)")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    models_trained: bool
    ollama_available: bool
    ollama_models: list[str]
    coder_model: str
    advisor_model: str


class AnalysisResponse(BaseModel):
    analysis: dict
    recommendations: list[dict]
    ml_prediction: dict | None = None
    llm_analysis: dict | None = None
    llm_mode: str = "static"
    chat_response: str = ""
    timestamp: str


class GenerateResponse(BaseModel):
    output: str
    file_type: str
    entry_name: str
    llm_mode: str = "static"
    chat_response: str = ""
    timestamp: str


class FullPackResponse(BaseModel):
    analysis: dict
    recommendations: list[dict]
    var_file: str

    tdr_file: str
    rexx_exec: str | None = None
    ml_prediction: dict | None = None
    llm_analysis: dict | None = None
    llm_mode: str
    coder_model: str
    advisor_model: str
    llm_errors: list[str] = []
    chat_response: str = ""
    timestamp: str


# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════

def _try_ml_predict(text: str) -> dict | None:
    """Attempt scikit-learn ML prediction. Returns None if models not trained."""
    try:
        from training.train_model import predict_entry_type
        return predict_entry_type(text)
    except (FileNotFoundError, ImportError, Exception):
        return None


def _parsed_to_summary(parsed) -> dict:
    """Convert ParsedEntry to a JSON-serialisable summary dict for LLM context."""
    return {
        "entry_name": parsed.name,
        "segment": parsed.segment,
        "purpose": parsed.purpose,
        "line_count": parsed.line_count,
        "statistics": {
            "variables": len(parsed.variables),
            "macros": len(parsed.macros),
            "branches": len(parsed.branches),
            "instructions": len(parsed.instructions),
            "file_operations": len(parsed.file_ops),
            "error_points": len(parsed.error_points),
            "ecb_references": len(parsed.ecb_refs),
            "labels": len(parsed.labels),
        },
        "macros_called": [m.name for m in parsed.macros],
        "macros": [m.name for m in parsed.macros],
        "file_references": parsed.file_ops,
        "ecb_references": parsed.ecb_refs,
        "labels": parsed.labels,
        "inputs": parsed.inputs,
        "outputs": parsed.outputs,
        "dependencies": parsed.dependencies,
        "variables": [
            {
                "name": v.name,
                "type": v.var_type,
                "length": v.length,
                "source": v.source,
                "description": v.description,
            }
            for v in parsed.variables
        ],
    }


# ═══════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Service health check — includes Ollama model availability."""
    models_ok = os.path.exists(
        os.path.join(os.path.dirname(__file__), "training", "data", "entry_type_model.joblib")
    )
    ollama_ok = is_ollama_available()
    models = list_available_models() if ollama_ok else []
    return HealthResponse(
        status="OK",
        service="STS Coder API",
        version="2.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        models_trained=models_ok,
        ollama_available=ollama_ok,
        ollama_models=models,
        coder_model=CODER_MODEL,
        advisor_model=ADVISOR_MODEL,
    )


@app.get("/api/models")
def get_models():
    """List locally available Ollama models."""
    available = list_available_models()
    return {
        "available": available,
        "coder_model": CODER_MODEL,
        "coder_ready": any(CODER_MODEL in m for m in available),
        "advisor_model": ADVISOR_MODEL,
        "advisor_ready": any(ADVISOR_MODEL in m for m in available),
        "ollama_available": is_ollama_available(),
    }


@app.post("/api/check")
def static_check(req: TPFEntryRequest):
    """Static code checker — rule-based analysis for critical z/TPF bugs."""
    code = req.raw_text or ""
    issues = []
    lines = code.splitlines()
    import re

    # Rule 1: FIWHC without hold release (UNFRC, FILEC, FILNC, FILUC)
    fiwhc_count = sum(1 for l in lines if "FIWHC" in l.upper() and not l.strip().startswith("*"))
    release_hold_count = sum(1 for l in lines if any(m in l.upper() for m in ["UNFRC", "FILEC", "FILNC", "FILUC"]) and not l.strip().startswith("*"))
    if fiwhc_count > 0 and release_hold_count == 0:
        issues.append({"severity": "ERROR", "rule": "FIWHC_NO_RELEASE",
            "message": f"FIWHC found ({fiwhc_count}x) but no release macro (UNFRC/FILEC/FILNC/FILUC) detected. File lock never released — will cause ECB deadlock.",
            "fix": "Add UNFRC, FILEC, FILNC, or FILUC before every EXITC and EXITN path."})
    elif fiwhc_count > release_hold_count:
        issues.append({"severity": "WARNING", "rule": "FIWHC_RELEASE_MISMATCH",
            "message": f"FIWHC count ({fiwhc_count}) exceeds release macro count ({release_hold_count}). Possible lock leak on error path.",
            "fix": "Ensure every error exit path also releases held file records."})

    # Rule 2: GETCC without storage release (RELCC, FILEC, FILEA, FILUC)
    getcc_count = sum(1 for l in lines if "GETCC" in l.upper() and not l.strip().startswith("*"))
    release_core_count = sum(1 for l in lines if any(m in l.upper() for m in ["RELCC", "FILEC", "FILEA", "FILUC"]) and not l.strip().startswith("*"))
    if getcc_count > 0 and release_core_count == 0:
        issues.append({"severity": "WARNING", "rule": "GETCC_NO_RELEASE",
            "message": f"GETCC found ({getcc_count}x) but no release macro (RELCC/FILEC/FILEA/FILUC) detected. Storage leak — core blocks never freed.",
            "fix": "Add RELCC, FILEC, FILEA, or FILUC before exit."})
    elif getcc_count > release_core_count:
        issues.append({"severity": "WARNING", "rule": "GETCC_RELEASE_MISMATCH",
            "message": f"GETCC count ({getcc_count}) exceeds release macro count ({release_core_count}). Storage may leak on error paths.",
            "fix": "Ensure every error exit path also releases core blocks."})

    # Rule 3: EXITC without EXITN (no error path)
    has_exitc = any("EXITC" in l.upper() for l in lines if not l.strip().startswith("*"))
    has_exitn = any("EXITN" in l.upper() for l in lines if not l.strip().startswith("*"))
    if has_exitc and not has_exitn:
        issues.append({"severity": "WARNING", "rule": "NO_EXITN",
            "message": "EXITC found but no EXITN. No error termination path defined.",
            "fix": "Add EXITN as the termination macro for all error paths."})

    # Rule 4: Subroutine return consistency
    has_backc = any("BACKC" in l.upper() for l in lines if not l.strip().startswith("*"))
    if has_backc and has_exitc:
        issues.append({"severity": "INFO", "rule": "BACKC_EXITC_MIX",
            "message": "Both BACKC (subroutine return) and EXITC (ECB termination) detected in the same program.",
            "fix": "Use BACKC for normal subroutine returns, and reserve EXITC for ECB-level termination paths."})

    # Rule 5: Check for self-modification patterns (non-reentrant)
    if "MVC" in code.upper() and any(kw in code.upper() for kw in ["CSECT", "DSECT"]):
        mvc_to_csect = [l for l in lines if "MVC" in l.upper() and not l.strip().startswith("*")]
        if mvc_to_csect:
            issues.append({"severity": "INFO", "rule": "REENTRANT_RISK",
                "message": "MVC instructions detected in code. Verify no writes target the CSECT itself (non-reentrant code).",
                "fix": "Move all modifiable data to ECB data levels or DSECT areas."})

    # Rule 6: FINDA without error check hint
    finda_count = sum(1 for l in lines if "FINDA" in l.upper() and not l.strip().startswith("*"))
    if finda_count > 0:
        # Check if condition code is tested or branches exist near FINDA
        issues.append({"severity": "INFO", "rule": "FINDA_RC_CHECK",
            "message": f"FINDA used ({finda_count}x). Ensure return code is checked (RC=4 = not found, RC=8 = I/O error).",
            "fix": "Test condition code after FINDA: BZ (record found), BNZ (not found / error)."})

    # Rule 7: Register R8 Modification (ECB Pointer)
    r8_modified = False
    for l in lines:
        if l.strip().startswith("*"):
            continue
        # Match instructions modifying R8 directly as destination
        if re.search(r"\b(L|LA|LR|SR|AR|S|A|AL|ALR|SL|SLR|CVB|CVD|LNR|LPR|LCR|LTR)\s+R8\b", l.upper()):
            r8_modified = True
            break
        # Check LM wrap-around loads
        lm_match = re.search(r"\b(LM)\s+(\w+)\s*,\s*(\w+)", l.upper())
        if lm_match:
            try:
                def get_reg_num(r):
                    r = r.strip()
                    if r.startswith("R"):
                        return int(r[1:])
                    return int(r)
                r_start = get_reg_num(lm_match.group(2))
                r_end = get_reg_num(lm_match.group(3))
                if r_start <= r_end:
                    if r_start <= 8 <= r_end:
                        r8_modified = True
                        break
                else:
                    if 8 >= r_start or 8 <= r_end:
                        r8_modified = True
                        break
            except Exception:
                pass
    if r8_modified:
        issues.append({"severity": "ERROR", "rule": "R8_MODIFICATION",
            "message": "Modification of register R8 detected. Register R8 is reserved as the ECB pointer in z/TPF and must not be altered.",
            "fix": "Use registers R0-R7 or R10-R15 for general operations."})

    # Rule 8: File Lock held across Defer/Wait (Deadlock Risk)
    has_fiwhc = any("FIWHC" in l.upper() for l in lines if not l.strip().startswith("*"))
    has_defer = any(any(d in l.upper() for d in ["DLAYC", "DEFRC", "WTOPC", "WAITC"]) for l in lines if not l.strip().startswith("*"))
    if has_fiwhc and has_defer:
        issues.append({"severity": "WARNING", "rule": "LOCK_ACROSS_DEFER",
            "message": "File lock (FIWHC) held while calling a defer/wait macro (DLAYC/DEFRC/WTOPC/WAITC). Holding database locks across defers can lead to severe ECB resource deadlocks.",
            "fix": "Release the lock using UNFRC or file/unhold the record before executing the defer macro."})

    if not issues:
        issues.append({"severity": "OK", "rule": "CLEAN",
            "message": "No critical issues detected. Code follows basic z/TPF safety rules.",
            "fix": None})

    return {"issues": issues, "total": len(issues),
            "errors": sum(1 for i in issues if i["severity"] == "ERROR"),
            "warnings": sum(1 for i in issues if i["severity"] == "WARNING")}


@app.get("/api/zcmd/list")
def zcmd_list():
    """Return all known Z-Commands for the browser panel."""
    from llm.tpf_knowledge import KNOWLEDGE, ZCMD_RESPONSES
    cmds = []
    for cmd, detail in ZCMD_RESPONSES.items():
        cmds.append({"cmd": cmd, "purpose": detail["purpose"],
                     "category": detail["category"], "syntax": detail["syntax"]})
    # Add remaining from simple KB
    for cmd, desc in KNOWLEDGE.get("z_commands", {}).items():
        if cmd not in ZCMD_RESPONSES:
            cmds.append({"cmd": cmd, "purpose": desc[:60] + ("..." if len(desc) > 60 else ""),
                         "category": "General", "syntax": cmd})
    cmds.sort(key=lambda x: x["cmd"])
    return {"commands": cmds, "total": len(cmds)}



@app.get("/api/stream/zcmd")
def stream_zcmd(command: str = ""):
    """SSE stream: explain a Z-Command. Rich KB-first, LLM fallback for unknowns."""
    def generate_llm():
        for token in explain_z_command_stream(command):
            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
        yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(generate_llm(), media_type="text/event-stream", headers=headers)


@app.get("/api/stream/chat")
def stream_chat(query: str = ""):
    """SSE stream: intelligent z/TPF copilot chat — KB-routed, topic-aware."""
    def generate():
        for token in chat_stream(query):
            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
        yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(generate(), media_type="text/event-stream", headers=headers)


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_entry(req: TPFEntryRequest):
    """Analyze a TPF entry — static + optional LLM (Qwen2.5-Coder + Llama 3.3)."""
    cached = GLOBAL_CACHE.get(req.raw_text, "analyze", req.mode, req.use_llm)
    if cached:
        log.info("[CACHE HIT] Serving /api/analyze from in-memory cache")
        return cached

    try:
        parsed = parse_tpf_entry(req.raw_text, req.entry_name, req.segment)
        analysis = generate_analysis(parsed)
        recs = generate_recommendations(parsed)
        ml = _try_ml_predict(req.raw_text)

        llm_analysis = None
        llm_recs = None
        llm_mode = "static"

        if req.use_llm and is_ollama_available():
            try:
                summary = _parsed_to_summary(parsed)
                # Qwen2.5-Coder: structural analysis
                llm_analysis = analyze_entry_llm(req.raw_text, summary)
                # Llama 3.3: recommendations with coder context
                llm_recs = generate_recommendations_llm(summary, coder_analysis=llm_analysis)
                llm_mode = "dual_model"
            except Exception as e:
                log.warning(f"LLM analyze failed: {e}")

        final_recs = llm_recs if llm_recs else recs

        resp = AnalysisResponse(
            analysis=analysis,
            recommendations=final_recs,
            ml_prediction=ml,
            llm_analysis=llm_analysis,
            llm_mode=llm_mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        GLOBAL_CACHE.set(req.raw_text, "analyze", req.mode, req.use_llm, resp)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/var", response_model=GenerateResponse)
def gen_var(req: TPFEntryRequest):
    """Generate VAR file — Qwen2.5-Coder (LLM) or static fallback."""
    cached = GLOBAL_CACHE.get(req.raw_text, "var", req.mode, req.use_llm)
    if cached:
        log.info("[CACHE HIT] Serving /api/generate/var from in-memory cache")
        return cached

    try:
        parsed = parse_tpf_entry(req.raw_text, req.entry_name, req.segment)
        llm_mode = "static"
        output = ""

        if req.use_llm and is_ollama_available():
            try:
                output = generate_var_llm(_parsed_to_summary(parsed))
                llm_mode = f"qwen2.5-coder"
            except Exception as e:
                log.warning(f"LLM VAR failed: {e}")

        if not output:
            output = generate_var_file(parsed)

        resp = GenerateResponse(
            output=output,
            file_type="VAR",
            entry_name=parsed.name,
            llm_mode=llm_mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        GLOBAL_CACHE.set(req.raw_text, "var", req.mode, req.use_llm, resp)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/api/generate/tdr", response_model=GenerateResponse)
def gen_tdr(req: TPFEntryRequest):
    """Generate TDR file — Qwen2.5-Coder (LLM) or static fallback."""
    cached = GLOBAL_CACHE.get(req.raw_text, "tdr", req.mode, req.use_llm)
    if cached:
        log.info("[CACHE HIT] Serving /api/generate/tdr from in-memory cache")
        return cached

    try:
        parsed = parse_tpf_entry(req.raw_text, req.entry_name, req.segment)
        llm_mode = "static"
        output = ""

        if req.use_llm and is_ollama_available():
            try:
                output = generate_tdr_llm(_parsed_to_summary(parsed))
                llm_mode = f"qwen2.5-coder"
            except Exception as e:
                log.warning(f"LLM TDR failed: {e}")

        if not output:
            output = generate_tdr_file(parsed)

        resp = GenerateResponse(
            output=output,
            file_type="TDR",
            entry_name=parsed.name,
            llm_mode=llm_mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        GLOBAL_CACHE.set(req.raw_text, "tdr", req.mode, req.use_llm, resp)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/rexx", response_model=GenerateResponse)
def gen_rexx(req: TPFEntryRequest):
    """Generate IBM z/TPF REXX (RAVEN) exec — Qwen2.5-Coder only."""
    cached = GLOBAL_CACHE.get(req.raw_text, "rexx", req.mode, req.use_llm)
    if cached:
        log.info("[CACHE HIT] Serving /api/generate/rexx from in-memory cache")
        return cached

    try:
        parsed = parse_tpf_entry(req.raw_text, req.entry_name, req.segment)

        summary = _parsed_to_summary(parsed)
        llm_mode = "static"
        output = ""

        if req.use_llm and is_ollama_available():
            try:
                output = generate_rexx_llm(summary)
                llm_mode = "qwen2.5-coder"
            except Exception as e:
                log.warning(f"LLM REXX failed: {e}")

        if not output:
            output = generate_rexx_static(summary)

        resp = GenerateResponse(
            output=output,
            file_type="REXX",
            entry_name=parsed.name,
            llm_mode=llm_mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        GLOBAL_CACHE.set(req.raw_text, "rexx", req.mode, req.use_llm, resp)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/explain", response_model=GenerateResponse)
def explain_zcmd(req: TPFEntryRequest):
    """Explain a single ZTPF Z Command — rich knowledge base first, LLM for unknowns."""
    try:
        from llm.tpf_knowledge import ZCMD_RESPONSES, parse_zcmd_verb
        cmd_text = req.raw_text.strip()
        base_cmd = parse_zcmd_verb(cmd_text)
        output = explain_z_command_llm(cmd_text)
        llm_mode = "knowledge_base" if ZCMD_RESPONSES.get(base_cmd) else (
            "qwen2.5-coder" if is_ollama_available() else "knowledge_base"
        )
        if not output:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown Z-Command '{base_cmd}'. Try ZDSYS, ZDECB, ZOSRV, or browse the Z-CMD panel.",
            )
        return GenerateResponse(
            output=output,
            file_type="ZCMD",
            entry_name="Z_CMD",
            llm_mode=llm_mode,
            chat_response=output,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=GenerateResponse)
def chat_only(req: TPFEntryRequest):
    """General ZTPF conversational endpoint — Dual model: Qwen answers, Llama refines."""
    try:
        from llm.tpf_knowledge import KNOWLEDGE
        query = req.raw_text.strip()
        
        # Check if this is a Z-command lookup
        first_word = query.split()[0].upper() if query else ""
        kb_entry = KNOWLEDGE.get("z_commands", {}).get(first_word)
        
        if kb_entry:
            output = explain_z_command_llm(query)
            from llm.tpf_knowledge import ZCMD_RESPONSES
            llm_mode = "knowledge_base" if ZCMD_RESPONSES.get(first_word) else "qwen2.5-coder"
            return GenerateResponse(
                output=output,
                file_type="CHAT",
                entry_name="CHAT",
                llm_mode=llm_mode,
                chat_response=output,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        
        if not is_ollama_available():
            # Fallback: search knowledge base for keywords
            query_lower = query.lower()
            matches = []
            for cmd, purpose in KNOWLEDGE.get("z_commands", {}).items():
                if any(w in purpose.lower() for w in query_lower.split() if len(w) > 3):
                    matches.append(f"  • **{cmd}**: {purpose}")
            if matches:
                output = f"Based on your query, here are relevant Z-Commands:\n\n" + "\n".join(matches[:5])
            else:
                output = "Ollama is offline. I can answer Z-Command lookups from my knowledge base. Try entering a specific Z-Command like ZDSYS or ZDECB."
            return GenerateResponse(
                output=output, file_type="CHAT", entry_name="CHAT",
                llm_mode="knowledge_base", chat_response=output,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # General conversational question — use Advisor (Llama) for best results
        from llm.ollama_client import ADVISOR_MODEL, CHAT_SYSTEM, _call_ollama
        prompt = f"""You are the STS Coder IBM z/TPF Engineering Copilot. Answer this question clearly and concisely:

{query}

Use your knowledge of IBM z/TPF, Z-Commands, REXX, VAR, TDR and TPF assembler."""
        output = _call_ollama(ADVISOR_MODEL, CHAT_SYSTEM, prompt, temperature=0.4)
        
        return GenerateResponse(
            output=output,
            file_type="CHAT",
            entry_name="CHAT",
            llm_mode=f"{ADVISOR_MODEL}",
            chat_response=output,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/full", response_model=FullPackResponse)
def gen_full(req: TPFEntryRequest):
    """
    Full Engineering Pack — dual-model reinforcement pipeline.
    Phase 1 (Qwen2.5-Coder): Analyze → VAR → TDR → REXX
    Phase 2 (Llama 3.3):     Recommendations using ALL Phase 1 outputs
    """
    cached = GLOBAL_CACHE.get(req.raw_text, "full", req.mode, req.use_llm)
    if cached:
        log.info("[CACHE HIT] Serving /api/generate/full from in-memory cache")
        return cached

    try:
        parsed = parse_tpf_entry(req.raw_text, req.entry_name, req.segment)
        static_analysis = generate_analysis(parsed)
        static_recs = generate_recommendations(parsed)
        ml = _try_ml_predict(req.raw_text)

        if req.use_llm and is_ollama_available():
            log.info("[FULL] Running dual-model reinforcement pipeline...")
            llm_result = run_full_pipeline_llm(req.raw_text, _parsed_to_summary(parsed))

            # Merge static analysis with LLM enhancements
            merged_analysis = {**static_analysis}
            if llm_result.get("analysis"):
                merged_analysis["llm_classification"] = llm_result["analysis"]

            chat_reply = f"I have successfully generated the Full Pack documentation using {llm_result['coder_model']}. "
            rec_count = len(llm_result["recommendations"] or static_recs)
            if rec_count > 0:
                chat_reply += f"The Advisor ({llm_result['advisor_model']}) has reviewed the code and identified {rec_count} recommendations. Please check the output tabs."
            else:
                chat_reply += "No major risks were found by the Advisor. Please review the output tabs."

            resp = FullPackResponse(
                analysis=merged_analysis,
                recommendations=llm_result["recommendations"] or static_recs,
                var_file=llm_result["var_file"] or generate_var_file(parsed),

                tdr_file=llm_result["tdr_file"] or generate_tdr_file(parsed),
                rexx_exec=llm_result.get("rexx_exec"),
                ml_prediction=ml,
                llm_analysis=llm_result.get("analysis"),
                llm_mode=llm_result["llm_mode"],
                coder_model=llm_result["coder_model"],
                advisor_model=llm_result["advisor_model"],
                llm_errors=llm_result.get("errors", []),
                chat_response=chat_reply,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            GLOBAL_CACHE.set(req.raw_text, "full", req.mode, req.use_llm, resp)
            return resp
        else:
            # Pure static fallback
            resp = FullPackResponse(
                analysis=static_analysis,
                recommendations=static_recs,
                var_file=generate_var_file(parsed),

                tdr_file=generate_tdr_file(parsed),
                rexx_exec=None,
                ml_prediction=ml,
                llm_analysis=None,
                llm_mode="static",
                coder_model=CODER_MODEL,
                advisor_model=ADVISOR_MODEL,
                llm_errors=["Ollama not available — using static generation."],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            GLOBAL_CACHE.set(req.raw_text, "full", req.mode, req.use_llm, resp)
            return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict")
def predict_entry(req: TPFEntryRequest):
    """Scikit-learn ML entry type and risk classification."""
    ml = _try_ml_predict(req.raw_text)
    if ml is None:
        raise HTTPException(
            status_code=503,
            detail="Models not trained. POST /api/train first.",
        )
    return {"prediction": ml, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/train")
def train_models():
    """Trigger scikit-learn model training pipeline on ZTPF training data."""
    try:
        from training.train_model import train
        metadata = train()
        return {
            "status": "TRAINING_COMPLETE",
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}\n{traceback.format_exc()}")


# ═══════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════

@app.on_event("startup")
async def startup():
    print("=" * 60)
    print("  STS Coder API v2.0 — Dual-Model LLM Edition")
    print("  Travelport Smart TPF System Coder")
    print("=" * 60)
    from llm.tpf_knowledge import ZCMD_RESPONSES
    print(f"  Z-Commands in knowledge base: {len(ZCMD_RESPONSES)}")
    ollama_ok = is_ollama_available()
    print(f"  Ollama available: {ollama_ok}")
    if ollama_ok:
        models = list_available_models()
        print(f"  Available models: {models}")
        print(f"  Coder model  ({CODER_MODEL}): {'[OK]' if any(CODER_MODEL in m for m in models) else '[NOT PULLED]'}")
        print(f"  Advisor model ({ADVISOR_MODEL}): {'[OK]' if any(ADVISOR_MODEL in m for m in models) else '[NOT PULLED]'}")
    else:
        print("  [WARN] Ollama not running -- KB + static fallback mode active")
        print("    To enable LLM: ollama serve && ollama pull qwen2.5-coder && ollama pull llama3.2")
    type_model = os.path.join(os.path.dirname(__file__), "training", "data", "entry_type_model.joblib")
    if not os.path.exists(type_model):
        try:
            from training.train_model import train
            print("  ML models not found — training classifiers...")
            train()
            print("  ML models trained successfully.")
        except Exception as e:
            print(f"  [WARN] ML auto-train skipped: {e}")
    else:
        try:
            from training.train_model import _load_models
            import threading
            threading.Thread(target=_load_models, name="STS-ModelLoader", daemon=True).start()
            print("  ML models loading in background...")
        except Exception as e:
            print(f"  [WARN] Failed to start background model load: {e}")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
