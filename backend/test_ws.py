"""Quick smoke-test for the /ws/agent WebSocket endpoint."""

import asyncio
import json

import websockets


async def main() -> None:
    uri = "ws://localhost:8000/ws/agent"

    async with websockets.connect(uri) as ws:
        # Send prompt
        await ws.send(json.dumps({"prompt": "Build a premium landing page for a SaaS product called CloudFlow"}))
        print(">>> Sent prompt. Waiting for streaming updates...\n")

        async for raw in ws:
            msg = json.loads(raw)
            msg_type = msg.get("type", "?")

            if msg_type == "node_update":
                node = msg.get("node", "?")
                state = msg.get("state", {})
                print(f"[node_update] {node}")
                for key, value in state.items():
                    if key == "messages":
                        for m in value:
                            print(f"  message ({m['role']}): {m['content'][:120]}...")
                    elif key == "files":
                        print(f"  files: {[f['filename'] for f in value]}")
                    else:
                        preview = str(value)[:120]
                        print(f"  {key}: {preview}")
                print()

            elif msg_type == "final":
                print("[final] Execution complete!")
                state = msg.get("state", {})
                print(f"  execution_success: {state.get('execution_success')}")
                print(f"  preview_url: {state.get('preview_url', '')}")
                print(f"  terminal_output: {str(state.get('terminal_output', ''))[:200]}")
                print()

            elif msg_type == "error":
                print(f"[error] {msg.get('detail')}")

            else:
                print(f"[unknown] {msg}")


if __name__ == "__main__":
    asyncio.run(main())
