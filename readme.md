# Olexi AI: Project Documentation

**Version:** 1.0
**Date:** July 27, 2025

## 1. Project Goal

The primary goal of the Olexi AI project is to significantly lower the barrier to entry for legal research on the AustLII database. By creating an intelligent conversational interface, we aim to empower students, legal professionals, and the general public to find and understand complex legal information using simple, natural language, thereby democratizing access to Australasian law.

## 2. Core Concept

Olexi AI is a browser extension that integrates seamlessly with the AustLII website. It provides a chat-based interface that acts as an expert research assistant.

Users can interact with Olexi AI in the following ways:

1.  **Natural Language Search:** A user can type a complex query in plain English (e.g., *"What are the key High Court cases related to the duty of care for public authorities?"*). Olexi AI will interpret this request, formulate a precise search query, and execute it.
2.  **AI-Powered Summarization:** Instead of just a list of links, Olexi AI returns a synthesized, human-readable summary of the most relevant findings, explaining the key points of legislation or the significance of case law.
3.  **Direct Citations & Full Results:** Every piece of information in the AI's summary is backed by direct, clickable links to the source documents on AustLII. Additionally, a link to the complete, raw search results page is provided, allowing for verification and deeper research.

## 3. The AustLII Technology Environment

Our initial research and testing have confirmed that AustLII does **not** provide a formal, documented public API for developers. Instead, the project's success relies on programmatically interacting with its user-facing search engine.

*   **De Facto API:** The "API" is the website's URL-driven search functionality. All searches are executed via `GET` requests to a specific endpoint with parameters encoded in the URL.
*   **The Live Endpoint:** All development must target the modern, reliable search endpoint:
    `https://www.austlii.edu.au/search/`
*   **Data Format:** The endpoint returns search results as a **raw HTML document**. There is no JSON response. This necessitates a server-side web scraping component to parse the HTML and extract structured data.
*   **Key Constraint - URL Length:** The AustLII server has a limit on the length of a `GET` request URL. A query that includes too many database filters will fail. Our application logic must account for this by using broad category filters for wide-ranging searches.

## 4. System Design and Architecture

The project is built on a robust, decoupled architecture consisting of a Python backend and a vanilla JavaScript browser extension. All communication between the backend and the LLM will adhere to the **Model Context Protocol (MCP)** for structure and reliability.

### 4.1. High-Level Diagram

```
+---------------------------+       (HTTPS API Call)       +----------------------------+
|                           |      (JSON Request/Resp)     |                            |
| Browser Extension         | <--------------------------> | Backend Server (Python)    |
| (Vanilla HTML/CSS/JS)     |                              | (Implements MCP Logic)     |
|                           |                              |                            |
+---------------------------+                              +-------------+--------------+
                                                                         |
                                                                         | (Server-side)
                                                                         |
+------------------------------------------------------------------------+-------------------+
|                                                                                            |
v (API Call using MCP Schema)                                     v (GET Request for HTML)
                                                                                            |
+----------------------------+                                  +----------------------------+
| LLM Service (e.g., OpenAI) |                                  | AustLII Server             |
+----------------------------+                                  +----------------------------+
```

### 4.2. The Five-Phase Workflow

1.  **Capture (Extension):** The browser extension captures the user's prompt and sends it to the backend.
2.  **Analyze & Strategize (Backend -> LLM Call #1):** The backend constructs an MCP-compliant request, including the user prompt and a list of available database tools. The LLM returns a structured JSON search plan.
3.  **Execute & Scrape (Backend -> AustLII):** The backend executes the plan by building the correct URL for the `/search/` endpoint, fetching the HTML, and scraping it into a clean list of result objects.
4.  **Synthesize & Formulate (Backend -> LLM Call #2):** The backend constructs a second MCP request, passing the scraped results to the LLM. The LLM returns a final, human-readable summary.
5.  **Deliver (Backend -> Extension):** The backend returns a final JSON object containing both the AI's summary and the URL of the raw search results page, which is then rendered by the extension according to the user's preference (link-in-chat vs. new tab).

## 5. Current Project State (as of July 27, 2025)

The project is currently at the **Functional Backend Prototype** stage. The core server-side logic has been implemented and validated.

### 5.1. Completed Milestones

*   **FastAPI Server Foundation:** A working server with a defined API endpoint (`/api/olexi-chat`) and correct CORS configuration is running.
*   **Web Scraper Module:** The `austlii_scraper.py` module can successfully query the AustLII `/search/` endpoint and parse the HTML to extract structured search results.
*   **MCP Handler Module:** The `mcp_handler.py` module is implemented, capable of making both "Strategist" and "Synthesizer" calls to the OpenAI API using a structured protocol.
*   **End-to-End Integration:** All backend modules are integrated. The server can receive a natural language prompt, execute the full five-phase workflow, and produce a final AI-generated summary based on live AustLII data.

### 5.2. Next Steps & To-Do

*   **Browser Extension Development:** The vanilla JS front-end needs to be built, including the chat UI, event listeners, and API `fetch` logic.
*   **Comprehensive Database Map:** The `database_map.py` needs to be expanded by reverse-engineering the codes for all key AustLII databases.
*   **Robust Error Handling:** Implement more sophisticated error handling for failed API calls, scraping errors, or malformed LLM responses.
*   **Deployment Plan:** Formulate a plan for deploying the Python backend to a production environment (e.g., Docker, cloud provider).
*   **Security & Scalability:** Refine CORS policies, implement rate limiting, and optimize performance.

## 6. Technology Stack

| Component | Technology | Framework/Library | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Server** | Python | FastAPI | Core API framework for handling requests. |
| | | Uvicorn | High-performance ASGI server to run the app. |
| | | Requests | Making HTTP `GET` requests to the AustLII server. |
| | | BeautifulSoup4 | Parsing and scraping the HTML responses from AustLII. |
| | | Pydantic | Defining and validating data models for API requests/responses. |
| | | python-dotenv | Managing environment variables and API keys securely. |
| **AI Communication** | Python | OpenAI Python SDK | Interacting with the OpenAI API service. |
| **Front-End** | JavaScript | Vanilla JS (ES6+) | All client-side logic, UI injection, and API calls. |
| | HTML5 / CSS3 | - | Structure and styling for the injected chat interface. |
| **AI Service** | LLM | OpenAI API | Providing the GPT-4 model for strategy and synthesis tasks. |


P.S. How to start: 
1. git clone.
2. Install and ictivate enviroment venv/conda.
3. `pip install -r requirements.txt`.
4. `uvicorn main:app --reload`.