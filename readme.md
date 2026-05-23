# E-commerce MCP Server

An MCP (Model Context Protocol) server that connects Claude to a SQLite e-commerce database using a schema-on-demand tool design.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Saran-Thangaraj/e-commernce-MCP-Server.git
cd e-commernce-MCP-Server
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up the database

```bash
cd sql
python setup_db.py    # creates e_commerce.db
python seed_data.py   # populates with sample data
```

### 4. Connect via Claude Desktop (recommended — no API key needed)

This server is designed to work with **Claude Desktop** as the client. You do not need an Anthropic API key — a free or Pro Claude.ai account is enough.

Add the following to your Claude Desktop config file:

**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "e-commerce": {
      "command": "python",
      "args": ["/absolute/path/to/e-commernce-MCP-Server/sql/mcp_server.py"]
    }
  }
}
```

Replace `/absolute/path/to/` with the actual path where you cloned the repo. Then restart Claude Desktop — the tools (`get_schema`, `preview_query`, `query_db`) will appear automatically.

### Alternative: Custom Python client (requires Anthropic API key)

If you want to build your own client instead of using Claude Desktop, you will need an API key from [console.anthropic.com](https://console.anthropic.com) and can use the `anthropic` library included in `requirements.txt`.

---

## Project Structure

```
e-commernce-MCP-Server/
├── sql/
│   ├── mcp_server.py   ← MCP server with 3 tools
│   ├── setup_db.py     ← creates the SQLite schema
│   ├── seed_data.py    ← populates sample e-commerce data
│   └── e_commerce.db   ← SQLite database
├── requirements.txt
├── .gitignore
└── readme.md
```

---

# MCP Tool Design: Schema-on-Demand

## Problem with embedding schema in tool descriptions

A naive approach puts the full table schema (column names, types) directly inside each tool's `description` field:

```
Tool(name="query_products", description="Columns: product_id, name, brand, category, ...")
Tool(name="query_orders",   description="Columns: order_id, customer_id, order_date, ...")
...
```

**Why this is bad:**
- The LLM reads every tool description on every call — even for tables it doesn't need
- Schema is hardcoded → breaks silently when columns are added or renamed
- As tables grow, token cost scales with the number of tables × columns

---

## Solution: Three-step schema-on-demand

Three tools are exposed to the LLM:

| Tool | Purpose |
|---|---|
| `get_schema` | Fetches live column names from the DB for a given table (or lists all tables) |
| `preview_query` | Dry-runs a SELECT and returns up to 5 sample rows for the user to review before committing |
| `query_db` | Runs the full SELECT SQL only after the user confirms the preview |

The schema is **never** embedded in tool descriptions. It enters the context only when the LLM explicitly asks for it.

---

## LLM call flow

```
User question
     │
     ▼
get_schema()              ← "What tables exist?"
     │  Available tables: products, customers, orders, order_items, payments
     ▼
get_schema("products")    ← "What columns does products have?"
     │  Table: products | Columns: product_id, name, brand, price, stock ...
     ▼
preview_query(sql=...)    ← LLM writes SQL and previews up to 5 rows
     │  Sample results shown to user for confirmation
     ▼
query_db(sql=...)         ← Full query executed only after user confirms
     │  Results
     ▼
Answer to user
```

---

## Why this works

- **Context efficient** — schema for unrelated tables never enters the context window
- **Always accurate** — `PRAGMA table_info()` reads from the live DB; no hardcoded strings to go stale
- **Works for any DB** — add a new table and `get_schema()` discovers it automatically; no code change needed
- **Separation of concerns** — schema discovery, preview, and query execution are independent tool calls
- **User confirmation gate** — `preview_query` adds a human-in-the-loop step: the LLM shows a 5-row sample and waits for approval before running the full query, preventing accidental large or unintended reads
