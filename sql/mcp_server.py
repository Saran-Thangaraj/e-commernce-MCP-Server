import os
import sys
import asyncio
import sqlite3
import mcp.server.stdio as stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, ServerCapabilities

# absolute path derived from the script location — works regardless of cwd
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e_commerce.db")
server  = Server("e-commerce-agent")

# ── DB helpers ────────────────────────────────────────────────────────────────
def list_tables() -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_schema(table_name: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = []
    for row in cursor.fetchall():
        tag = " [PK]" if row[5] else ""
        columns.append(f"{row[1]} ({row[2]}){tag}")
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fks = [f"{row[3]} → {row[2]}.{row[4]}" for row in cursor.fetchall()]
    conn.close()
    lines = [f"Table: `{table_name}`"]
    lines.append("  Columns : " + ", ".join(columns))
    if fks:
        lines.append("  FK joins : " + " | ".join(fks))
    return "\n".join(lines)

def run_query(sql: str) -> list:
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError(f"Only SELECT queries are allowed. Got: {sql.strip()[:50]}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return rows


# ── tools ─────────────────────────────────────────────────────────────────────
# list_tools() fires once when the MCP server starts.
# The client (e.g. Claude Desktop) reads these tool definitions and passes them
# to the LLM alongside every user message. The LLM decides which tool to call
# based on the user's question and the tool descriptions below.
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_schema",
            description=(
                "Call this first before writing any SQL. "
                "Returns table columns with types, which column is the Primary Key, "
                "and Foreign Key relationships (which column joins to which table). "
                "Pass a table_name to inspect one table, or omit to list all available tables."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table to inspect. Omit to list all table names."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="preview_query",
            description=(
                "Preview the results of a SELECT query without executing it. "
                "Useful for testing and debugging queries before running them."
                "call this before query_db so users can see the results and review it. "
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A valid SELECT SQL query."
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="query_db",
            description=(
                "Execute a read-only SELECT query on the e-commerce database only after previewing it. "
                "Always call get_schema first to confirm column names and joins. "
                "Only SELECT statements accepted — INSERT, UPDATE, DELETE, DROP will be rejected."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A valid SELECT SQL query."
                    }
                },
                "required": ["sql"]
            }
        ),
    ]


# ── tool handler ──────────────────────────────────────────────────────────────
# call_tool() is invoked by the client after the LLM picks a tool.
# It receives the tool name and arguments as JSON (parsed into a Python dict),
# calls the appropriate DB helper, converts the result to a plain string,
# and returns it as TextContent so the LLM can read it and form a response.
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_schema":
        table_name = arguments.get("table_name")
        if table_name:
            result = get_table_schema(table_name)
        else:
            result = "Available tables: " + ", ".join(list_tables())
        return [TextContent(type="text", text=result)]
    
    if name == "preview_query":
        sql = arguments["sql"].strip()
        if not sql.upper().startswith("SELECT"):
            return [TextContent(type="text", text=f"Rejected: Only SELECT queries allowed. Got: {sql[:50]}")]
        # run with LIMIT 5 so user sees a sample without pulling all rows
        preview_sql = sql if "LIMIT" in sql.upper() else sql + " LIMIT 5"
        try:
            rows = run_query(preview_sql)
            sample = "\n".join(str(row) for row in rows) or "No rows returned."
        except Exception as e:
            return [TextContent(type="text", text=f"Preview failed: {e}")]
        text = (
            f"SQL to be executed:\n{sql}\n\n"
            f"Sample results (up to 5 rows):\n{sample}\n\n"
            "Please confirm with the user before calling query_db to run the full query."
        )
        return [TextContent(type="text", text=text)]



    if name == "query_db":
        sql = arguments["sql"]
        try:
            rows = run_query(sql)
            text = "\n".join(str(row) for row in rows) or "No results found."
        except ValueError as e: 
            text = f"Rejected: {e}" ## LLM reads this message and understands the query was rejected, and can adjust the query and try again.
        return [TextContent(type="text", text=text)]

    return [TextContent(
        type="text",
        text=f"Tool '{name}' not found. Available tools: get_schema, preview_query, query_db."
    )]


# ── entry point ───────────────────────────────────────────────────────────────
async def main():
    print(f"E-commerce MCP server starting... DB={DB_PATH}", file=sys.stderr)
    async with stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="e-commerce-agent",
                server_version="1.0.0",
                capabilities=ServerCapabilities()
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
