# 🧠 Codebase Atlas: MCP Flight Booking POC

This document serves as a high-level navigational map and architectural reference for the `mcp-flight-booking-poc` project. It is intended for developers, researchers, and AI agents who need to understand the internal mechanics and integration patterns.

---

## 🏛 Core Architectural Layers

### 1. **Transport Layer (Server Entry Points)**
The project supports dual-mode operation for different lifecycle stages:
- **Stdio Entry (`server/app/main.py`)**: Uses **FastMCP** for seamless integration with the **MCP Inspector** or other interprocess-based hosts (e.g., local CLI agents).
- **HTTP/REST Entry (`server/app/server_http.py`)**: A **FastAPI** wrapper that translates RESTful `GET/POST` requests into tool calls. This enables multi-client support and Docker containerization.

### 2. **Logic Layer (Tools & Lifecycle)**
The "brain" of the MCP server resides in `server/app/tools/`. Each tool is structured to handle its own input validation and data interactions:
- `search_flights.py`: Flight search logic with filters.
- `book_flight.py`: Reservation persistence.
- `cancel_booking.py`: Booking state management.
- `list_bookings.py`: Transaction history retrieval.

### 3. **Persistence Layer (Data)**
Mock data and state are stored in the `server/data/` directory. JSON is used for simplicity and ease of inspection:
- `flights.json`: Static flight catalog (seed data).
- `bookings.json`: Dynamic reservation record (writeable).
- `airports.json`: Reference metadata for completions/suggestions.
- `company_policies.md`: Markdown resource provided to clients for knowledge-based reasoning.

### 4. **Client Layer (Consumption)**
Two primary clients demonstrate the versatility of the server:
- `client/demo_client.py`: A procedural script that tests individual endpoints via HTTP REST.
- `client/ai_agent.py`: An autonomous LLM-powered agent using **Llama 3.2 (via Ollama)**. This client consumes the server's tool registry and prompts to perform high-level tasks like "Find me a cheap flight to Rome and book it for John Doe."

---

## 🛠 Feature Highlights

| Feature | Implementation | Description |
| :--- | :--- | :--- |
| **Tool Execution** | `@mcp.tool()` | Typed Python functions with Pydantic for schema generation. |
| **Prompts** | `@mcp.prompt()` | Structural templates for common search queries. |
| **Autocompletion** | `mcp.completion()` | Returns airport suggestions as the user types (e.g. 'P' -> 'Paris'). |
| **Resources** | `@mcp.resource()` | Dynamic data URIs like `flights://catalog` or `bookings://current`. |

---

## 🚦 Operational Procedures

### **Development & Debugging**
1. Run the MCP Inspector: `npx @modelcontextprotocol/inspector python server/app/main.py`
2. This allows you to verify tool signatures, test prompts, and view resource data in a GUI.

### **Production Simulation (Docker)**
1. `docker-compose -f docker/docker-compose.yml up --build`
2. This spins up the FastAPI server, exposing it on port `8000`, ready for remote or local REST clients.

### **Integration Testing**
1. Ensure the server is running (HTTP mode).
2. Run `python client/demo_client.py` to verify the end-to-end booking flow.

---

## 📂 Mapping the Project Tree

```text
mcp-flight-booking-poc/
├── client/                     # Client ecosystem
│   ├── ai_agent.py             # LLM logic (Llama 3.2 / Ollama)
│   ├── demo_client.py          # Procedural test script
│   └── pyproject.toml          # Client deps
├── docker/                     # Infrastructure as Code
│   ├── Dockerfile              # Multi-stage server build
│   └── docker-compose.yml      # Orchestration
├── docs/                       # Project Documentation
│   ├── assets/                 # Brand assets & logos
│   ├── setup.md                # Install details
│   ├── usage.md                # Usage guide
│   └── deployment.md           # Cloud/Docker notes
├── server/                     # MCP Server Core
│   ├── app/                    # Codebase root
│   │   ├── main.py             # FastMCP (Stdio) entrypoint
│   │   ├── server_http.py      # FastAPI (HTTP/REST) entrypoint
│   │   ├── config.py           # Settings management
│   │   ├── middleware/         # Auth & CORS
│   │   └── tools/              # MCP Tool implementations
│   ├── data/                   # Persistence layer (JSON)
│   └── pyproject.toml          # Server deps
├── README.md                   # Brand landing page
├── LICENSE                     # MIT License
└── CODEBASE_INDEX.md           # (You are here) - Architectural overview
```
