import re

with open('backend/llm/ollama_client.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix generate_tdr_llm
old_tdr = '''    if var_output:
        context += f"\\nVAR File:\\n{var_output[:600]}\\n"
    if tdrv_output:
        context += f"\\nTDRV File:\\n{tdrv_output[:600]}\\n"'''
code = code.replace(old_tdr, '')

# Fix run_full_pipeline_llm
old_phase1 = '''    # Phase 1a: Coder — structural analysis
    try:
        log.info(f"[LLM] Phase 1a: {CODER_MODEL} — entry analysis")
        result["analysis"] = analyze_entry_llm(raw_text, parsed_summary)
    except Exception as e:
        result["errors"].append(f"Coder analysis: {e}")

    # Phase 1b: Coder — VAR file
    try:
        log.info(f"[LLM] Phase 1b: {CODER_MODEL} — VAR generation")
        result["var_file"] = generate_var_llm(parsed_summary)
    except Exception as e:
        result["errors"].append(f"VAR generation: {e}")

    # Phase 1c: Coder — TDRV (with VAR context = reinforcement)
    try:
        log.info(f"[LLM] Phase 1c: {CODER_MODEL} — TDRV generation")
        result["tdrv_file"] = generate_tdrv_llm(parsed_summary, result["var_file"] or None)
    except Exception as e:
        result["errors"].append(f"TDRV generation: {e}")

    # Phase 1d: Coder — TDR (with VAR+TDRV context = reinforcement)
    try:
        log.info(f"[LLM] Phase 1d: {CODER_MODEL} — TDR generation")
        result["tdr_file"] = generate_tdr_llm(
            parsed_summary,
            result["var_file"] or None,
            result["tdrv_file"] or None
        )
    except Exception as e:
        result["errors"].append(f"TDR generation: {e}")

    # Phase 1e: Coder — REXX exec
    try:
        log.info(f"[LLM] Phase 1e: {CODER_MODEL} — REXX generation")
        result["rexx_exec"] = generate_rexx_llm(parsed_summary)
    except Exception as e:
        result["errors"].append(f"REXX generation: {e}")'''

new_phase1 = '''    # Phase 1: Run all Coder generation tasks in parallel
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
            result["rexx_exec"] = res_rexx'''

code = code.replace(old_phase1, new_phase1)

with open('backend/llm/ollama_client.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Replaced')
