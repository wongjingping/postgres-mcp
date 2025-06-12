import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import asyncpg
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import sqlparse

load_dotenv()

PORT = 8050
# Database configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "housing")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Global connection pool
pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage database connection pool lifecycle"""
    global pool

    # Initialize connection pool on startup
    pool = await asyncpg.create_pool(
        DATABASE_URL, min_size=1, max_size=10, command_timeout=60
    )

    try:
        yield {"pool": pool}
    finally:
        # Clean up on shutdown
        if pool:
            await pool.close()


# Create MCP server
mcp = FastMCP("postgres-mcp-server", lifespan=lifespan, port=PORT)

UNSAFE_KEYWORDS = ["DELETE", "DROP", "UPDATE"]
def check_sql_injection(sql: str) -> bool:
    """
    Check if the SQL query contains any SQL injection patterns.
    """
    # parse with sqlparse and check for injection patterns
    parsed = sqlparse.parse(sql)
    # check if DELETE, DROP, or UPDATE is in the query
    for statement in parsed:
        for token in statement.tokens:
            if (token.ttype and 
                token.ttype in (sqlparse.tokens.Keyword, sqlparse.tokens.Keyword.DML, sqlparse.tokens.Keyword.DDL) and 
                token.value.upper() in UNSAFE_KEYWORDS):
                return True
    return False


@mcp.tool()
async def query_database(sql: str, params: Optional[List[Any]] = None) -> str:
    """
    Execute a SQL query against the PostgreSQL database.

    Args:
        sql: The SQL query to execute
        params: Optional list of parameters for the query (for parameterized queries)

    Returns:
        JSON string containing the query results
    """
    if not pool:
        return json.dumps({"error": "Database connection not available"})

    # Basic SQL injection protection - only allow SELECT statements
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed"})

    try:
        async with pool.acquire() as conn:
            if params:
                records = await conn.fetch(sql, *params)
            else:
                records = await conn.fetch(sql)

            # Convert records to list of dictionaries
            results = [dict(record) for record in records]

            return json.dumps(
                {"success": True, "data": results, "row_count": len(results)},
                default=str,
            )  # default=str handles datetime/decimal serialization

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_table_schema(table_name: str) -> str:
    """
    Get the schema information for a specific table.

    Args:
        table_name: Name of the table to describe

    Returns:
        JSON string containing table schema information
    """
    if not pool:
        return json.dumps({"error": "Database connection not available"})

    try:
        async with pool.acquire() as conn:
            # Get column information
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = $1 
                ORDER BY ordinal_position
            """

            columns = await conn.fetch(columns_query, table_name)

            if not columns:
                return json.dumps(
                    {"success": False, "error": f"Table '{table_name}' not found"}
                )

            schema_info = {
                "success": True,
                "table_name": table_name,
                "columns": [dict(col) for col in columns],
            }

            return json.dumps(schema_info, default=str)

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def list_tables() -> str:
    """
    List all tables in the current database.

    Returns:
        JSON string containing list of table names
    """
    if not pool:
        return json.dumps({"error": "Database connection not available"})

    try:
        async with pool.acquire() as conn:
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """

            records = await conn.fetch(tables_query)
            tables = [record["table_name"] for record in records]

            return json.dumps({"success": True, "tables": tables, "count": len(tables)})

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.resource("postgres://schema")
async def get_database_schema() -> str:
    """Get complete database schema information"""
    if not pool:
        return "Database connection not available"

    try:
        async with pool.acquire() as conn:
            # Get all tables and their columns
            schema_query = """
                SELECT 
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE t.table_schema = 'public'
                ORDER BY t.table_name, c.ordinal_position
            """

            records = await conn.fetch(schema_query)

            # Group by table
            schema = {}
            for record in records:
                table_name = record["table_name"]
                if table_name not in schema:
                    schema[table_name] = []

                schema[table_name].append(
                    {
                        "column": record["column_name"],
                        "type": record["data_type"],
                        "nullable": record["is_nullable"],
                        "default": record["column_default"],
                    }
                )

            return json.dumps(schema, indent=2, default=str)

    except Exception as e:
        return f"Error retrieving schema: {str(e)}"


if __name__ == "__main__":
    mcp.run()
