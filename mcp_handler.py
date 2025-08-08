# mcp_handler.py

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
from typing import List, Dict

# Load environment variables from .env file
load_dotenv()

# --- NEW SDK INITIALIZATION ---
# Create a client instance using the new SDK's 'genai.Client'
# It automatically picks up the GOOGLE_API_KEY from the .env file.
try:
    client = genai.Client()
except Exception as e:
    raise ValueError(f"Failed to initialize Google GenAI Client. Is GOOGLE_API_KEY set in your .env file? Error: {e}")


def generate_search_plan(user_prompt: str, database_tools: List[Dict]) -> Dict:
    """
    MCP Strategist Call: Takes a user prompt and generates a structured search plan using the new google-genai SDK.
    """
    system_prompt = f"""
    You are a legal research query expert for the AustLII database.
    Your task is to analyze the user's request and create a precise boolean search query
    and select the most relevant databases to search.

    You must respond in a valid JSON object format with two keys:
    1.  `query`: A string containing the boolean search query.
    2.  `databases`: A list of database codes selected from the tools provided.

    Available database tools:
    {json.dumps(database_tools, indent=2)}
    """

    print("--- MCP [Strategist] Call using google-genai SDK ---")
    
    # --- NEW SDK CALL SYNTAX ---
    response = client.models.generate_content(
        model='gemini-2.5-flash', # Or your preferred model
        contents=f"{system_prompt}\n\nUser Request: {user_prompt}",
        config=types.GenerateContentConfig(
            response_mime_type='application/json'
        )
    )
    
    plan_str = response.text
    print(f"Received search plan: {plan_str}")
    return json.loads(plan_str)


def summarize_results(user_prompt: str, scraped_data: List[Dict]) -> str:
    """
    MCP Synthesizer Call: Takes scraped data and generates a human-readable summary using the new google-genai SDK.
    """
    system_prompt = """
    You are Olexi AI, an expert legal research assistant.
    Your goal is to provide a clear, concise, and helpful summary based *only* on the
    search results provided to you.

    You must adhere to the following rules:
    1.  Base your answer *exclusively* on the provided data. Do not use any external knowledge.
    2.  If the data is empty, inform the user that you could not find any relevant documents.
    3.  Format your answer using Markdown.
    4.  Cite your sources by embedding hyperlinks into your summary, like this: `[Document Title](URL)`.
    """
    
    tool_data_str = json.dumps(scraped_data, indent=2)

    print("--- MCP [Synthesizer] Call using google-genai SDK ---")

    full_prompt = (
        f"{system_prompt}\n\n"
        f"User's original question: '{user_prompt}'\n\n"
        f"Here is the data I found for you to summarize:\n{tool_data_str}"
    )
    
    # --- NEW SDK CALL SYNTAX ---
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=full_prompt
    )

    summary = response.text
    print(f"Generated summary: {summary}")
    return summary