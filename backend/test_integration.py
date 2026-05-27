"""Quick integration test for STS Coder backend."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from parser.tpf_parser import parse_tpf_entry
from generators.var_generator import generate_var_file
from generators.tdr_generator import generate_tdr_file
from analyzer.entry_analyzer import generate_analysis, generate_recommendations
from training.train_model import predict_entry_type
from llm import (is_ollama_available, generate_rexx_static,
    CODER_MODEL, ADVISOR_MODEL)

print("=" * 60)
print("  STS Coder — Integration Test")
print("=" * 60)

print(f"  Coder Model:   {CODER_MODEL}")
print(f"  Advisor Model: {ADVISOR_MODEL}")
print(f"  Ollama:        {is_ollama_available()}")

sample = """TR00     CSECT
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         CLI   0(R3),C'A'
         BNE   ERR0010
         GETCC R5,SIZE=256
         LTR   R15,R15
         BNZ   ERR0020
         FILEC R4,LEV=1,TYPE=FACE
         LTR   R15,R15
         BNZ   ERR0030
         MVC   OUTPUT_DATA,0(R4)
OUTPUT_DATA DS CL100
WORK_LOC DS    CL6
INPUT_LOC DS   CL6
ERR_CODE DS    CL4
         RELCC R5
         EXITC TRDR
ERR0010  DS    0H
         MVI   ERR_CODE,C'1'
         BACKC TRDR
ERR0020  DS    0H
         MVI   ERR_CODE,C'2'
         EXITN TRDR
ERR0030  DS    0H
         RELCC R5
         MVI   ERR_CODE,C'3'
         EXITN TRDR"""

parsed = parse_tpf_entry(sample, "TR00", "CUSTPROF")
print(f"\n[PARSE]  {parsed.name} | {len(parsed.variables)} vars | {len(parsed.macros)} macros | {len(parsed.branches)} branches")

var = generate_var_file(parsed)
has_raven = all(k in var for k in ["VARIATION_DESCRIPTION", "START_UP_TASKS", "VARIATION_CMD", "TRAP", "SHUTDOWN_TASKS"])
print(f"[VAR]    {len(var)} chars | RAVEN format: {has_raven}")

tdr = generate_tdr_file(parsed)
print(f"[TDR]    {len(tdr)} chars")

analysis = generate_analysis(parsed)
print(f"[ANLYS]  {len(analysis)} keys | complexity={analysis.get('complexity_score',{}).get('level','?')}")

recs = generate_recommendations(parsed)
print(f"[RECS]   {len(recs)} recommendations")

ml = predict_entry_type(sample)
print(f"[ML]     type={ml['entry_type']} ({ml['entry_type_confidence']:.1%}) | risk={ml['risk_level']} ({ml['risk_level_confidence']:.1%})")

rexx = generate_rexx_static({"entry_name": "TR00", "macros_called": ["ENTER", "FILEC", "EXITC"], "purpose": "File access"})
has_raven_rexx = "ADDRESS RAVEN" in rexx
print(f"[REXX]   {len(rexx)} chars | ADDRESS RAVEN: {has_raven_rexx}")

print("\n" + "=" * 60)
errors = []
if not has_raven: errors.append("VAR missing RAVEN sections")
if not has_raven_rexx: errors.append("REXX missing ADDRESS RAVEN")
if len(parsed.variables) == 0: errors.append("No variables parsed")
if len(parsed.macros) == 0: errors.append("No macros parsed")

if errors:
    print("  FAILED: " + ", ".join(errors))
else:
    print("  ALL TESTS PASSED")
print("=" * 60)
