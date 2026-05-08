import httpx, time

start = time.time()
with httpx.Client(timeout=10) as client:
    with client.stream("GET", "http://127.0.0.1:8100/api/stream/zcmd?command=ZDSYS") as r:
        for line in r.iter_lines():
            if line.startswith("data:"):
                print(line)
        
print(f"\nTime: {time.time()-start:.2f}s")
