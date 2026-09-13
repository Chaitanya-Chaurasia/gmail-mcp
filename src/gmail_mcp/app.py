"""Shared FastMCP instance.

Lives in its own module so tool modules can import it without circular
imports (server.py imports the tools, tools import the app).
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gmail")
