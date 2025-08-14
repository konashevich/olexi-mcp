# Start MCP server locally (root path)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn mcp_http:app --host 127.0.0.1 --port 3000 --reload
```

Test handshake:

```bash
curl -s -X POST http://127.0.0.1:3000/ \
  -H 'Content-Type: application/json' \
  -d '{"method":"initialize","params":{}}' | jq
```

Point your MCP host to: http://127.0.0.1:3000/
