# MCP Postgres Server

A Model Context Protocol server for querying PostgreSQL databases with tools for data retrieval and schema inspection.

## Setup

**Prerequisites**: Python 3.11+ and PostgreSQL

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database connection (defaults shown)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_DB=housing
```

## Usage

**Development**

Run the following command to start the server in development mode and launch the MCP Inspector:

```bash
mcp dev main.py
```

**MCP Client Integration**

```json
{
  "mcpServers": {
    "postgres": {
      "command": "python",
      "args": ["main.py"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres",
        "POSTGRES_DB": "housing"
      }
    }
  }
}
```

## Available Tools

- **`query_database`** - Execute SELECT queries (with SQL injection protection)
- **`get_table_schema`** - Get table column information and constraints  
- **`list_tables`** - List all database tables
- **`postgres://schema`** - Access complete database schema (resource)

## Security

- Only `SELECT` statements allowed
- Parameterized queries supported
- Environment-based configuration (no hardcoded credentials) 