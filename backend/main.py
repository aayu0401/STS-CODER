"""
STS Coder — FastAPI Backend Server  (v2.0 — Dual-Model LLM)
=============================================================
Travelport Smart TPF System Coder API

Models:
  Qwen2.5-Coder  → IBM REXX, VAR, TDRV, TRD generation (ZTPF Z Command trained)
  Llama 3.3      → Engineering recommendations & risk narrative
  Reinforcement  → Coder outputs feed Advisor for cross-model refinement

Endpoints:
  POST /api/analyze            — Analyze TPF entry (static + LLM)
  POST /api/generate/var       — Generate VAR file (LLM-powered)
  POST /api/generate/tdrv      — Generate TDRV file (LLM-powered)
  POST /api/generate/trd       — Generate TRD file (LLM-powered)
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
import traceback
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sts.main")

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(__file__))

from parser.tpf_parser import parse_tpf_entry
from generators.var_generator import generate_var_file
from generators.tdrv_generator import generate_tdrv_file
from generators.trd_generator import generate_trd_file
from analyzer.entry_analyzer import generate_analysis, generate_recommendations
from llm import (
    is_ollama_available,
    list_available_models,
    run_full_pipeline_llm,
    generate_var_llm,
    generate_tdrv_llm,
    generate_trd_llm,
    generate_rexx_llm,
    generate_recommendations_llm,
    analyze_entry_llm,
    explain_z_command_llm,
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
        "**Qwen2.5-Coder** handles IBM REXX, VAR, TDRV, TRD generation.\n"
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


# ═══════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════

class TPFEntryRequest(BaseModel):
    raw_text: str = Field(..., min_length=1, description="Raw TPF assembly / REXX / description text")
    entry_name: str = Field("", description="Optional entry name override")
    segment: str = Field("", description="Optional segment name")
    mode: str = Field("FULL", description="Output mode: ANALYZE, VAR, TDRV, TRD, REXX, FULL")
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
    timestamp: str


class GenerateResponse(BaseModel):
    output: str
    file_type: str
    entry_name: str
    llm_mode: str = "static"
    timestamp: str


class FullPackResponse(BaseModel):
    analysis: dict
    recommendations: list[dict]
    var_file: str
    tdrv_file: str
    trd_file: str
    rexx_exec: str | None = None
    ml_prediction: dict | None = None
    llm_analysis: dict | None = None
    llm_mode: str
    coder_model: str
    advisor_model: str
    llm_errors: list[str] = []
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


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_entry(req: TPFEntryRequest):
    """Analyze a TPF entry — static + optional LLM (Qwen2.5-Coder + Llama 3.3)."""
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

        return AnalysisResponse(
            analysis=analysis,
            recommendations=final_recs,
            ml_prediction=ml,
            llm_analysis=llm_analysis,
            llm_mode=llm_mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/var", response_model=GenerateResponse)
def gen_var(req: TPFEntryRequest):
    """Generate VAR file — Qwen2.5-Coder (LLM) or static fallback."""
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

        return GenerateResponse(
            output=output,
            file_type="VAR",
            entry_name=parsed.name,
            llm_mode=llm_mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/tdrv", response_model=GenerateResponse)
def gen_tdrv(req: TPFEntryRequest):
    """Generate TDRV file — Qwen2.5-Coder (LLM) or static fallback."""
    try:
        parsed = parse_tpf_entry(req.raw_text, req.entry_name, req.segment)
        llm_mode = "static"
        output = ""

        if req.use_llm and is_ollama_available():
            try:
                output = generate_tdrv_llm(_parsed_to_summary(parsed))
                llm_mode = f"qwen2.5-coder"
            except Exception as e:
                log.warning(f"LLM TDRV failed: {e}")

        if not output:
            output = generate_tdrv_file(parsed)

        return GenerateResponse(
            output=output,
            file_type="TDRV",
            entry_name=parsed.name,
            llm_mode=llm_mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/trd", response_model=GenerateResponse)
def gen_trd(req: TPFEntryRequest):
    """Generate TRD file — Qwen2.5-Coder (LLM) or static fallback."""
    try:
        parsed = parse_tpf_entry(req.raw_text, req.entry_name, req.segment)
        llm_mode = "static"
        output = ""

        if req.use_llm and is_ollama_available():
            try:
                output = generate_trd_llm(_parsed_to_summary(parsed))
                llm_mode = f"qwen2.5-coder"
            except Exception as e:
                log.warning(f"LLM TRD failed: {e}")

        if not output:
            output = generate_trd_file(parsed)

        return GenerateResponse(
            output=output,
            file_type="TRD",
            entry_name=parsed.name,
            llm_mode=llm_mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/rexx", response_model=GenerateResponse)
def gen_rexx(req: TPFEntryRequest):
    """Generate IBM z/TPF REXX (RAVEN) exec — Qwen2.5-Coder only."""
    try:
        parsed = parse_tpf_entry(req.raw_text, req.entry_name, req.segment)

        if not is_ollama_available():
            raise HTTPException(
                status_code=503,
                detail="Ollama not available. Start Ollama and pull qwen2.5-coder to use REXX generation."
            )

        output = generate_rexx_llm(_parsed_to_summary(parsed))
        return GenerateResponse(
            output=output,
            file_type="REXX",
            entry_name=parsed.name,
            llm_mode=f"qwen2.5-coder",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/explain", response_model=GenerateResponse)
def explain_zcmd(req: TPFEntryRequest):
    """Explain a single ZTPF Z Command — Qwen2.5-Coder only."""
    try:
        if not is_ollama_available():
            raise HTTPException(
                status_code=503,
                detail="Ollama not available. Start Ollama and pull qwen2.5-coder to use Z-CMD explanation."
            )

        output = explain_z_command_llm(req.raw_text.strip())
        return GenerateResponse(
            output=output,
            file_type="ZCMD",
            entry_name="Z_CMD",
            llm_mode=f"qwen2.5-coder",
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
    Phase 1 (Qwen2.5-Coder): Analyze → VAR → TDRV → TRD → REXX
    Phase 2 (Llama 3.3):     Recommendations using ALL Phase 1 outputs
    """
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

            return FullPackResponse(
                analysis=merged_analysis,
                recommendations=llm_result["recommendations"] or static_recs,
                var_file=llm_result["var_file"] or generate_var_file(parsed),
                tdrv_file=llm_result["tdrv_file"] or generate_tdrv_file(parsed),
                trd_file=llm_result["trd_file"] or generate_trd_file(parsed),
                rexx_exec=llm_result.get("rexx_exec"),
                ml_prediction=ml,
                llm_analysis=llm_result.get("analysis"),
                llm_mode=llm_result["llm_mode"],
                coder_model=llm_result["coder_model"],
                advisor_model=llm_result["advisor_model"],
                llm_errors=llm_result.get("errors", []),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        else:
            # Pure static fallback
            return FullPackResponse(
                analysis=static_analysis,
                recommendations=static_recs,
                var_file=generate_var_file(parsed),
                tdrv_file=generate_tdrv_file(parsed),
                trd_file=generate_trd_file(parsed),
                rexx_exec=None,
                ml_prediction=ml,
                llm_analysis=None,
                llm_mode="static",
                coder_model=CODER_MODEL,
                advisor_model=ADVISOR_MODEL,
                llm_errors=["Ollama not available — using static generation."],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
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
    ollama_ok = is_ollama_available()
    print(f"  Ollama available: {ollama_ok}")
    if ollama_ok:
        models = list_available_models()
        print(f"  Available models: {models}")
        print(f"  Coder model  ({CODER_MODEL}): {'✓' if any(CODER_MODEL in m for m in models) else '✗ not pulled'}")
        print(f"  Advisor model ({ADVISOR_MODEL}): {'✓' if any(ADVISOR_MODEL in m for m in models) else '✗ not pulled'}")
    else:
        print("  ⚠ Ollama not running — static fallback mode active")
        print("    To enable LLM: ollama serve && ollama pull qwen2.5-coder && ollama pull llama3.3")
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
