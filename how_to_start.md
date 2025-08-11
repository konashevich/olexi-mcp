How to start: 
1. git clone.
2. Install and activate environment venv/conda.
3. `pip install -r requirements.txt`.
4. `uvicorn main:app --reload --port 3000`.

Server will be available at:
- **Landing Page:** http://127.0.0.1:3000 (Olexi branded homepage)
- **API Documentation:** http://127.0.0.1:3000/docs (Interactive FastAPI docs)
- **Status:** http://127.0.0.1:3000/status (Server + AI flag)

Features Available:
- ✅ Professional Olexi branding with favicon support
- ✅ Comprehensive Australian legal database coverage (65+ databases)
- ✅ AI-powered planning and summarization via Tools Bridge
- ✅ Progressive Web App manifest for mobile experience
- ✅ Static file serving for assets and documentation

How to run API test:
1.  **Start the Server:**
    If your server isn't running, start it again from your terminal:
    ```bash
    uvicorn main:app --reload --port 3000
    ```

2.  **Try the Tools Bridge:**
    *   In `/docs`, expand these endpoints in order:
        - `GET /api/tools/databases`
        - `POST /api/tools/plan_search` (requires AI; provide a prompt like "negligence")
        - `POST /api/tools/search_austlii` (use the plan's query and databases)
        - `POST /api/tools/summarize_results` (requires AI; feed the scraped results)

**Expected Result:** You'll see valid databases, an AI-generated plan when AI is available, real AustLII results from the scraper, and a concise AI summary.

Tip: Check `GET /austlii/health` and `GET /austlii/uptime` for AustLII availability and recent uptime.