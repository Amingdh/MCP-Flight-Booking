#!/usr/bin/env python3
"""
MCP Flight Booking — AI Agent (Llama 3 via Ollama)
====================================================
An LLM-powered MCP host that:
  1. Connects to the MCP Flight Booking server
  2. Fetches the available tools manifest
  3. Passes tool definitions to Llama 3.2 (via Ollama)
  4. Executes tool calls the LLM decides to make
  5. Returns to the LLM with results until it produces a final natural-language answer

Usage:
    python ai_agent.py
    python ai_agent.py --query "Find me a cheap flight from Paris to Rome on April 1st 2026 and book it for John Smith"
    python ai_agent.py --base-url http://localhost:8000 --ollama-url http://localhost:11434 --model llama3.2
"""

import argparse
import json
import sys
import httpx

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL   = "http://localhost:8000"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL      = "llama3.2"
DEFAULT_API_KEY    = "DEMO_KEY"

# ── Tool Schema Helpers ───────────────────────────────────────────────────────

# These are static schemas matching what the MCP server exposes.
# In a full implementation these would be built from the tool manifest dynamically.
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search for available flights by origin, destination, and date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin":      {"type": "string", "description": "Departure city, e.g. 'Paris'"},
                    "destination": {"type": "string", "description": "Arrival city, e.g. 'Rome'"},
                    "date":        {"type": "string", "description": "Travel date in YYYY-MM-DD format"},
                },
                "required": ["origin", "destination", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "Book a seat on a given flight for a passenger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_id":      {"type": "string", "description": "The flight ID to book, e.g. 'FL002'"},
                    "passenger_name": {"type": "string", "description": "Full name of the passenger"},
                },
                "required": ["flight_id", "passenger_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_bookings",
            "description": "List all confirmed flight bookings on record.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_flights_catalog",
            "description": "Retrieve the full raw catalog of EVERY flight available in the database. Use this if search_flights returns no results to see what dates/cities actually exist.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_policies",
            "description": "Read the official airline policies document. Use this when a user asks about baggage limits, cancellation rules, refund eligibility, pet travel, or any company policy topic.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_airports_info",
            "description": "Read detailed information about airports, including terminal count, transit options to the city, and lounges. Use this before booking a flight if the user asks for travel advice.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking",
            "description": "Cancel a confirmed flight booking by its booking ID. Use this when the user explicitly asks to cancel or remove a booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {"type": "string", "description": "The booking ID to cancel, e.g. 'BKA5FD8367'"},
                },
                "required": ["booking_id"],
            },
        },
    },
]


# ── MCP Tool Executor ─────────────────────────────────────────────────────────

def execute_tool(client: httpx.Client, base_url: str, tool_name: str, arguments: dict) -> str:
    """Call the MCP server to execute a tool and return its result as a JSON string."""
    endpoint_map = {
        "search_flights":        ("POST", f"{base_url}/tools/searchFlights"),
        "book_flight":           ("POST", f"{base_url}/tools/bookFlight"),
        "list_bookings":         ("GET",  f"{base_url}/tools/listBookings"),
        "get_flights_catalog":   ("GET",  f"{base_url}/resources/flights"),
        "get_company_policies":  ("GET",  f"{base_url}/resources/policies"),
        "get_airports_info":     ("GET",  f"{base_url}/resources/airports"),
        "cancel_booking":        ("POST", f"{base_url}/tools/cancelBooking"),
    }

    if tool_name not in endpoint_map:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    # Tools that take no parameters: ignore any hallucinated args from small models
    NO_PARAMS_TOOLS = {"get_flights_catalog", "get_company_policies", "list_bookings", "get_airports_info"}

    method, url = endpoint_map[tool_name]
    try:
        if method == "POST":
            resp = client.post(url, json=arguments)
        else:
            safe_params = {} if tool_name in NO_PARAMS_TOOLS else arguments
            resp = client.get(url, params=safe_params)
        resp.raise_for_status()
        
        data = resp.json()

        # 🚀 THE FIX: Programmatic fallback to the Resource
        if tool_name == "search_flights" and data.get("total_found") == 0:
            print("\n    " + "━" * 50)
            print("    ⚠️  0 results returned by tool 'search_flights'.")
            print("    🔄  Programmatically fetching MCP Resource: [flights://catalog]")
            print("    " + "━" * 50 + "\n", flush=True)
            
            # Fetch the catalog automatically, saving the LLM a step
            catalog_resp = client.get(f"{base_url}/resources/flights")
            catalog_resp.raise_for_status()
            
            return json.dumps({
                "search_results": data,
                "SYSTEM_CRITICAL_INSTRUCTION": "You MUST NOT combine the user's requested cities with the catalog flights. The user asked for a route that DOES NOT EXIST. Tell them NO flights exist for their route, and list ONLY EXACTly what is written in the available_catalog below.",
                "available_catalog": catalog_resp.json()
            })

        return json.dumps(data)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}: {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Ollama Chat ───────────────────────────────────────────────────────────────

def chat_with_llm(ollama_url: str, model: str, messages: list[dict]) -> dict:
    """Send a chat request to Ollama and return the response message."""
    payload = {
        "model":    model,
        "messages": messages,
        "tools":    TOOL_DEFINITIONS,
        "stream":   False,
    }
    with httpx.Client(timeout=120.0) as http:
        resp = http.post(f"{ollama_url}/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json()["message"]


# ── Agentic Loop ──────────────────────────────────────────────────────────────

def run_agent(query: str, base_url: str, ollama_url: str, model: str, api_key: str) -> None:
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    print(f"\n🤖  MCP + Llama Flight Agent")
    print(f"    Model  : {model}")
    print(f"    Server : {base_url}")
    print("─" * 60)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI Flight Booking and Airport Info Assistant. "
                "CRITICAL INSTRUCTIONS:\n"
                "1. Wait for the user to explicitly ask to search or book a flight before calling search_flights. "
                "2. If the user asks about an airport, terminals, or transit, immediately call the 'get_airports_info' tool first!\n"
                "3. If the user asks about luggage, pets, or cancellations, call the 'get_company_policies' tool.\n"
                "4. You are working with MOCK DATA stored in a JSON file. Flights exist ONLY for specific dates in April 2026. "
                "NEVER make up or hallucinate flight prices, airlines, schedules, or airport information if they are not in the tool results. "
                "If search_flights returns 0 results, DO NOT pretend there are flights. Use 'get_flights_catalog' to see what data is actually available.\n"
                "5. NEVER write or output Python code (e.g. `<|python_tag|>`). You do NOT have a code interpreter. You MUST use the official tool calling format to look up information."
            ),
        }
    ]

    with httpx.Client(headers=headers, timeout=30.0) as mcp_client:
        if query:
            print(f"User: {query}\n")
            _process_query(query, messages, mcp_client, base_url, ollama_url, model)
        else:
            print("Chat session started. Type 'exit' or 'quit' to end.")
            while True:
                try:
                    user_input = input("\nYou: ").strip()
                    if user_input.lower() in ["exit", "quit"]:
                        break
                    if not user_input:
                        continue
                        
                    _process_query(user_input, messages, mcp_client, base_url, ollama_url, model)
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break

def _process_query(query: str, messages: list[dict], mcp_client: httpx.Client, base_url: str, ollama_url: str, model: str):
    messages.append({"role": "user", "content": query})
    max_steps = 10
    
    for step in range(max_steps):
        print(f"\n⚙️  Step {step + 1}: Calling LLM...", flush=True)
        response_msg = chat_with_llm(ollama_url, model, messages)
        messages.append(response_msg)

        tool_calls = response_msg.get("tool_calls") or []
        content = response_msg.get("content", "").strip()

        # Hack for small models like Llama 3.2 3B:
        # Sometimes it hallucinates raw JSON in the text content alongside conversational text.
        if not tool_calls and "{" in content and "}" in content:
            start_idx = content.find('{"name"')
            if start_idx == -1:
                start_idx = content.find('{"function"')
                
            if start_idx != -1:
                end_idx = content.rfind("}")
                if end_idx >= start_idx:
                    json_str = content[start_idx:end_idx+1]
                    try:
                        parsed = json.loads(json_str)
                        if "name" in parsed:
                            tool_calls = [{"function": {"name": parsed["name"], "arguments": parsed.get("parameters", {})}}]
                            response_msg["content"] = content[:start_idx].strip() # keep the prefix text if any
                    except json.JSONDecodeError:
                        pass

        if not tool_calls:
            # No tool calls → LLM has produced its final answer
            print("\n" + "═" * 60)
            print("🧠  Agent Response:")
            print("═" * 60)
            print(response_msg.get("content", "").strip())
            print("═" * 60)
            return

        # Execute each tool the LLM requested
        for tc in tool_calls:
            fn      = tc["function"]
            name    = fn["name"]
            # Ollama returns arguments as a string or dict depending on version
            args    = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}

            print(f"    🔧 Calling tool: {name}({json.dumps(args)})", flush=True)
            result = execute_tool(mcp_client, base_url, name, args)
            res_str = str(result)
            print(f"    ✅ Result: {res_str[:200]}{'...' if len(res_str) > 200 else ''}")

            # Feed the tool result back into the conversation
            messages.append({
                "role":    "tool",
                "content": result,
            })

    print("\n⚠️  Max steps reached without a final answer.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MCP Flight Booking AI Agent (Llama 3 via Ollama)")
    parser.add_argument(
        "--query",
        default="",
        help="Natural language query for the agent. If omitted, starts an interactive chat.",
    )
    parser.add_argument("--base-url",   default=DEFAULT_BASE_URL,   help="MCP server base URL")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL,  help="Ollama base URL")
    parser.add_argument("--model",      default=DEFAULT_MODEL,       help="Ollama model name")
    parser.add_argument("--api-key",    default=DEFAULT_API_KEY,     help="MCP server API key")
    args = parser.parse_args()

    # Quick health check on Ollama
    try:
        with httpx.Client(timeout=5.0) as http:
            r = http.get(f"{args.ollama_url}/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            if not any(args.model in m for m in models):
                print(f"\n❌  Model '{args.model}' not found in Ollama.")
                print(f"    Available models: {models or 'none'}")
                print(f"    Pull it first: docker exec mcp-ollama ollama pull {args.model}")
                sys.exit(1)
    except Exception as e:
        print(f"\n❌  Cannot reach Ollama at {args.ollama_url}: {e}")
        sys.exit(1)

    run_agent(
        query=args.query,
        base_url=args.base_url,
        ollama_url=args.ollama_url,
        model=args.model,
        api_key=args.api_key,
    )


if __name__ == "__main__":
    main()
