# Olexi AI: Project Documentation (Definitive Edition)

**Version:** 2.0
**Date:** July 27, 2025

## 1. Project Goal

The primary goal of the Olexi AI project is to significantly lower the barrier to entry for legal research on the AustLII database. By creating an intelligent conversational interface, we aim to empower users to find and understand complex legal information using simple, natural language.

## 2. Core Concept

Olexi AI is a browser extension that integrates seamlessly with the AustLII website, providing a chat-based interface that acts as an expert research assistant. It interprets natural language queries, formulates and executes precise searches against the AustLII engine, and returns a synthesized, human-readable summary with direct citations and a link to the full search results.

## 3. The AustLII Technology Environment: An Experimental Deep Dive

Initial development has revealed that AustLII's search functionality is non-trivial to interact with programmatically. The system is a legacy CGI application with undocumented security measures. Our success is contingent on understanding and correctly mimicking the behavior of a real browser interacting with its web forms. The following findings were retrieved experimentally and are critical to the project's function.

### 3.1. The Endpoint: The `cgi-bin` Ground Truth

*   **Finding:** Despite the presence of modern-looking URLs like `/search/` on the site, extensive testing confirmed that this endpoint is a deliberate dead end for our purposes, returning a `410 Gone` HTTP status.
*   **Decision:** The one true, functional endpoint for all search queries is the legacy CGI script:
    `https://www.austlii.edu.au/cgi-bin/sinosrch.cgi`
*   **Rationale:** All successful manual search submissions from the site's own forms ultimately resolve to this endpoint. It is the only reliable entry point for programmatic searching.

### 3.2. Request Method & Security: Simulating a Real Browser

*   **Finding:** A simple `GET` request to a fully-formed `cgi-bin` URL fails when accessed directly (e.g., pasting into a browser or using a basic script). However, network inspection of a successful manual search confirmed the request method is indeed `GET`.
*   **The Tricky Issue:** This paradox is resolved by the server's use of HTTP header validation to block non-browser requests. The server expects requests to "prove" they originated from a legitimate user interaction on the website.
*   **Decision:** All `GET` requests sent by our scraper **must** include specific HTTP headers to mimic a real browser.
*   **Rationale:** Experimental testing identified two critical headers:
    1.  `User-Agent`: Identifies our script as a standard web browser, preventing it from being blocked as a bot.
    2.  `Referer`: Tells the server that the request is "coming from" the official search form page. This is a common, simple security measure to prevent direct linking and scraping.
    By including these headers, our script's requests become indistinguishable from a real user's, ensuring they are accepted and processed.

### 3.3. URL Parameter Encoding: The "Repeating Key" Logic

*   **Finding:** When filtering by multiple databases, the AustLII server does not accept a comma-separated list.
*   **The Tricky Issue:** The server expects the parameter key for the database filter (`mask_path`) to be repeated for each value.
*   **Decision:** Our Python code must construct the URL parameters as a *list of tuples* rather than a standard dictionary.
*   **Rationale:** This specific data structure forces the `requests` library to generate the correct URL format (e.g., `...?mask_path=A&mask_path=B`), satisfying the server's requirement. An incorrect format would lead to a logical error where the server returns "0 documents found" because the query is impossible to fulfill.

### 3.4. HTML Structure & Parsing Strategy: A Non-Semantic Environment

*   **Finding:** The HTML of the search results page is not structured semantically. The desired content (the actual results) is mixed in with other UI elements like sorting tabs and navigation links.
*   **The Tricky Issue:** A naive parser that simply looks for the first list on the page (`<ul>`) will incorrectly scrape the sorting tabs ("By Relevance", "By Database", etc.) instead of the actual legal documents.
*   **Decision:** The scraper employs a two-step parsing strategy.
*   **Rationale:** To ensure accuracy, the parser must first isolate the unique parent container that holds *only* the search results. Through inspection of the `debug_austlii_page.html` file, this was identified as `<div class="card">`. Only after isolating this container does the parser then search for the individual result items, which are identified as `<li class="multi">`. This precision prevents the scraper from capturing irrelevant UI elements.

## 4. System Design and Architecture

Our initial research and testing have confirmed that AustLII does **not** provide a formal, documented public API for developers. Instead, the project's success relies on programmatically interacting with its user-facing search engine.
The project uses a decoupled architecture with a Python/FastAPI backend and a vanilla JavaScript browser extension. The backend acts as the central orchestrator, implementing the Model Context Protocol (MCP) for reliable communication with the LLM and housing the specialized scraper module designed to handle the intricacies of the AustLII environment.

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
4. `uvicorn main:app --reload --port 3000`.