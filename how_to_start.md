How to start: 
1. git clone.
2. Install and activate environment venv/conda.
3. `pip install -r requirements.txt`.
4. Create favicon image files (see FAVICON_SETUP.md for instructions).
5. `uvicorn main:app --reload --port 3000`.

Server will be available at:
- **Landing Page:** http://127.0.0.1:3000 (Olexi branded homepage)
- **API Documentation:** http://127.0.0.1:3000/docs (Interactive FastAPI docs)
- **Health Check:** http://127.0.0.1:3000/health (Server status)

Features Available:
- ✅ Professional Olexi branding with favicon support
- ✅ Comprehensive Australian legal database coverage (65+ databases)
- ✅ AI-powered legal research via /api/olexi-chat endpoint
- ✅ Progressive Web App manifest for mobile experience
- ✅ Static file serving for assets and documentation

How to run API test:
1.  **Start the Server:**
    If your server isn't running, start it again from your terminal:
    ```bash
    uvicorn main:app --reload --port 3000
    ```

2.  **Test the Endpoint:**
    *   Go to your interactive API docs at `http://127.0.0.1:3000/docs`.
    *   Expand the `POST /api/olexi-chat` endpoint.
    *   Click "Try it out".
    *   In the request body, enter a real legal term for the prompt, like `"negligence"`.
    *   Click "Execute".

**Expected Result:** You should now see a JSON response where the `ai_response` field contains a formatted list of the **top 3 actual search results** scraped directly from the AustLII website, complete with titles and clickable links.

You have now built a critical piece of the infrastructure! The server can successfully query and parse the target website. The next logical step will be to implement the MCP handler to orchestrate the LLM calls that will generate the search parameters and synthesize these results.