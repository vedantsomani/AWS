import asyncio
import json
import websockets

async def test():
    uri = 'ws://127.0.0.1:8000/ws/agent'
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"prompt": "build a simple counter app"}))
        while True:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=120)
                data = json.loads(resp)
                ftype = data.get("type", "")
                agent = data.get("agent", data.get("node", ""))
                print(f"{ftype}: {agent}")
                if ftype == "node_update" and "state" in data:
                    s = data["state"]
                    for key in ["files", "frontend_files", "backend_files", "database_files", "devops_files"]:
                        if key in s and s[key]:
                            print(f"  -> {len(s[key])} files in {key}")
                if ftype == "final":
                    files = data.get("state", {}).get("files", [])
                    print(f"FINAL: {len(files)} files")
                    if files:
                        for f in files:
                            print(f"  - {f.get('path', f.get('filename', 'unknown'))}")
                    break
            except asyncio.TimeoutError:
                print("Timeout")
                break

asyncio.run(test())
