"""Live API test — hit all endpoints."""
import json, time
try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except ImportError:
    print("ERROR: urllib not available")
    exit(1)

BASE = "http://localhost:8100"

def post(path, data):
    req = Request(f"{BASE}{path}", data=json.dumps(data).encode(), headers={"Content-Type": "application/json"}, method="POST")
    resp = urlopen(req, timeout=30)
    return json.loads(resp.read())

def get(path):
    resp = urlopen(f"{BASE}{path}", timeout=10)
    return json.loads(resp.read())

sample = """TR00     CSECT
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         CLI   0(R3),C'A'
         BNE   ERR0010
         GETCC R5,SIZE=256
         FILEC R4,LEV=1,TYPE=FACE
         MVC   OUTPUT_DATA,0(R4)
OUTPUT_DATA DS CL100
ERR_CODE DS    CL4
         RELCC R5
         EXITC TRDR
ERR0010  DS    0H
         MVI   ERR_CODE,C'1'
         EXITN TRDR"""

body = {"raw_text": sample, "entry_name": "TR00", "segment": "CUSTPROF", "use_llm": False}

print("=" * 60)
print("  STS Coder API — Live Test")
print("=" * 60)

# Health
h = get("/api/health")
print(f"[HEALTH]  status={h['status']} ollama={h['ollama_available']} models_trained={h['models_trained']}")

# Models
m = get("/api/models")
print(f"[MODELS]  coder_ready={m['coder_ready']} advisor_ready={m['advisor_ready']}")

# Static Checker
c = post("/api/check", {"raw_text": "ENTER TRDR\n FIWHC R4\n GETCC R5\n EXITC TRDR"})
print(f"[CHECK]   issues={c['total']} errors={c['errors']} warnings={c['warnings']}")

# Analyze
a = post("/api/analyze", body)
print(f"[ANALYZE] complexity={a['analysis']['complexity_score']['level']} ml_type={a.get('ml_prediction',{}).get('entry_type','N/A')}")

# Generate VAR
v = post("/api/generate/var", body)
has_raven = "VARIATION_DESCRIPTION" in v["output"] and "TRAP" in v["output"]
print(f"[VAR]     {len(v['output'])} chars | RAVEN_format={has_raven} | mode={v['llm_mode']}")

# Generate TDR
d = post("/api/generate/tdr", body)
print(f"[TDR]     {len(d['output'])} chars | mode={d['llm_mode']}")

# Generate REXX
r = post("/api/generate/rexx", body)
has_raven_rexx = "ADDRESS RAVEN" in r["output"]
print(f"[REXX]    {len(r['output'])} chars | RAVEN={has_raven_rexx} | mode={r['llm_mode']}")

# Full Pack
f = post("/api/generate/full", body)
print(f"[FULL]    var={len(f['var_file'])}c tdr={len(f['tdr_file'])}c recs={len(f['recommendations'])} mode={f['llm_mode']}")

# Predict
p = post("/api/predict", {"raw_text": sample})
print(f"[PREDICT] type={p['prediction']['entry_type']} risk={p['prediction']['risk_level']}")

# Z-CMD List
z = get("/api/zcmd/list")
print(f"[ZCMD]    {z['total']} commands in knowledge base")

print("=" * 60)
print("  ALL API ENDPOINTS PASSED")
print("=" * 60)
