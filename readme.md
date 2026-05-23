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
