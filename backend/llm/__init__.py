"""LLM — Ollama dual-model client for STS Coder."""
from .ollama_client import (
    is_ollama_available,
    list_available_models,
    run_full_pipeline_llm,
    generate_var_llm,
    generate_tdr_llm,
    generate_rexx_llm,
    generate_rexx_static,
    generate_recommendations_llm,
    analyze_entry_llm,
    explain_z_command_llm,
    explain_z_command_stream,
    chat_stream,
    CODER_MODEL,
    ADVISOR_MODEL,
    CHAT_SYSTEM,
)

__all__ = [
    "is_ollama_available",
    "list_available_models",
    "run_full_pipeline_llm",
    "generate_var_llm",
    "generate_tdr_llm",
    "generate_rexx_llm",
    "generate_rexx_static",
    "generate_recommendations_llm",
    "analyze_entry_llm",
    "explain_z_command_llm",
    "explain_z_command_stream",
    "chat_stream",
    "CODER_MODEL",
    "ADVISOR_MODEL",
    "CHAT_SYSTEM",
]

