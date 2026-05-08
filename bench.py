import httpx, time, json

start = time.time()
payload = {
    "model": "qwen2.5-coder:1.5b",
    "prompt": "Explain ZDSYS command in 2 sentences.",
    "stream": False,
    "options": {"num_predict": 80, "temperature": 0.1}
}
r = httpx.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=60)
data = r.json()
elapsed = time.time() - start
print(f"Time: {elapsed:.1f}s")
print(f"Tokens generated: {data.get('eval_count', '?')}")
print(f"Tokens/sec: {data.get('eval_count',0)/elapsed:.1f}")
print(f"Response: {data.get('response','')[:300]}")
