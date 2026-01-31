#!/usr/bin/env python3
"""
MCP Server for creating and managing markdown ticket files in Obsidian vault.
This server provides tools to create, read, update, and list ticket files.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Target directory for tickets
TICKETS_DIR = Path("/Users/danielmo/Desktop/Daniel/Real Estate Project")

# Ensure the directory exists
TICKETS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize MCP server
app = Server("obsidian-ticket-manager")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for ticket management."""
    return [
        Tool(
            name="create_ticket",
            description="Create a new markdown ticket file in the Obsidian vault",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the ticket (will be used as filename and header)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the ticket"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Priority level of the ticket",
                        "default": "medium"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorizing the ticket",
                        "default": []
                    },
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in-progress", "done", "blocked"],
                        "description": "Current status of the ticket",
                        "default": "todo"
                    }
                },
                "required": ["title", "description"]
            }
        ),
        Tool(
            name="update_ticket",
            description="Update an existing ticket file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename of the ticket to update (e.g., 'TICKET-001.md')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Updated description (optional)"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Updated priority (optional)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in-progress", "done", "blocked"],
                        "description": "Updated status (optional)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes to append (optional)"
                    }
                },
                "required": ["filename"]
            }
        ),
        Tool(
            name="list_tickets",
            description="List all ticket files in the vault",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in-progress", "done", "blocked", "all"],
                        "description": "Filter by status (default: all)",
                        "default": "all"
                    }
                }
            }
        ),
        Tool(
            name="read_ticket",
            description="Read the contents of a specific ticket file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename of the ticket to read (e.g., 'TICKET-001.md')"
                    }
                },
                "required": ["filename"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "create_ticket":
        return await create_ticket(arguments)
    elif name == "update_ticket":
        return await update_ticket(arguments)
    elif name == "list_tickets":
        return await list_tickets(arguments)
    elif name == "read_ticket":
        return await read_ticket(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def create_ticket(args: dict) -> list[TextContent]:
    """Create a new ticket file."""
    title = args["title"]
    description = args["description"]
    priority = args.get("priority", "medium")
    tags = args.get("tags", [])
    status = args.get("status", "todo")
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '-' for c in title)
    safe_title = safe_title.replace(' ', '-')[:50]  # Limit length
    filename = f"TICKET-{timestamp}-{safe_title}.md"
    filepath = TICKETS_DIR / filename
    
    # Create ticket content in markdown format
    content = f"""# {title}

## Metadata
- **Status**: {status}
- **Priority**: {priority}
- **Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Tags**: {', '.join(f'#{tag}' for tag in tags) if tags else 'None'}

## Description
{description}

## Notes
- 

## Updates

---
*Ticket ID: {filename.replace('.md', '')}*
"""
    
    # Write the file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return [TextContent(
            type="text",
            text=f"✓ Ticket created successfully!\n\nFilename: {filename}\nPath: {filepath}\n\nContent:\n{content}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"✗ Error creating ticket: {str(e)}"
        )]


async def update_ticket(args: dict) -> list[TextContent]:
    """Update an existing ticket file."""
    filename = args["filename"]
    filepath = TICKETS_DIR / filename
    
    if not filepath.exists():
        return [TextContent(
            type="text",
            text=f"✗ Error: Ticket file '{filename}' not found in {TICKETS_DIR}"
        )]
    
    try:
        # Read existing content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update fields if provided
        if "status" in args:
            content = update_field(content, "Status", args["status"])
        
        if "priority" in args:
            content = update_field(content, "Priority", args["priority"])
        
        if "description" in args:
            content = update_section(content, "Description", args["description"])
        
        if "notes" in args:
            # Append to Updates section
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_entry = f"- [{timestamp}] {args['notes']}\n"
            content = append_to_section(content, "Updates", update_entry)
        
        # Write updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return [TextContent(
            type="text",
            text=f"✓ Ticket updated successfully!\n\nFilename: {filename}\n\nUpdated content:\n{content}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"✗ Error updating ticket: {str(e)}"
        )]


async def list_tickets(args: dict) -> list[TextContent]:
    """List all ticket files."""
    status_filter = args.get("status", "all")
    
    try:
        # Get all .md files
        ticket_files = sorted(TICKETS_DIR.glob("TICKET-*.md"))
        
        if not ticket_files:
            return [TextContent(
                type="text",
                text=f"No tickets found in {TICKETS_DIR}"
            )]
        
        # Parse and filter tickets
        tickets = []
        for filepath in ticket_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            status = extract_field(content, "Status")
            priority = extract_field(content, "Priority")
            title = content.split('\n')[0].replace('# ', '').strip()
            
            if status_filter == "all" or status == status_filter:
                tickets.append({
                    "filename": filepath.name,
                    "title": title,
                    "status": status,
                    "priority": priority
                })
        
        # Format output
        if not tickets:
            result = f"No tickets with status '{status_filter}' found."
        else:
            result = f"Found {len(tickets)} ticket(s)"
            if status_filter != "all":
                result += f" with status '{status_filter}'"
            result += f" in {TICKETS_DIR}:\n\n"
            
            for ticket in tickets:
                result += f"📋 {ticket['filename']}\n"
                result += f"   Title: {ticket['title']}\n"
                result += f"   Status: {ticket['status']} | Priority: {ticket['priority']}\n\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"✗ Error listing tickets: {str(e)}"
        )]


async def read_ticket(args: dict) -> list[TextContent]:
    """Read a specific ticket file."""
    filename = args["filename"]
    filepath = TICKETS_DIR / filename
    
    if not filepath.exists():
        return [TextContent(
            type="text",
            text=f"✗ Error: Ticket file '{filename}' not found in {TICKETS_DIR}"
        )]
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return [TextContent(
            type="text",
            text=f"Contents of {filename}:\n\n{content}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"✗ Error reading ticket: {str(e)}"
        )]


# Helper functions
def extract_field(content: str, field_name: str) -> str:
    """Extract a metadata field value from ticket content."""
    for line in content.split('\n'):
        if f"**{field_name}**:" in line:
            return line.split(':', 1)[1].strip()
    return "unknown"


def update_field(content: str, field_name: str, new_value: str) -> str:
    """Update a metadata field in ticket content."""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if f"**{field_name}**:" in line:
            lines[i] = f"- **{field_name}**: {new_value}"
            break
    return '\n'.join(lines)


def update_section(content: str, section_name: str, new_content: str) -> str:
    """Update an entire section in ticket content."""
    lines = content.split('\n')
    in_section = False
    new_lines = []
    
    for i, line in enumerate(lines):
        if line.startswith(f"## {section_name}"):
            in_section = True
            new_lines.append(line)
            new_lines.append(new_content)
        elif in_section and line.startswith("## "):
            in_section = False
            new_lines.append(line)
        elif not in_section:
            new_lines.append(line)
    
    return '\n'.join(new_lines)


def append_to_section(content: str, section_name: str, new_content: str) -> str:
    """Append content to a section."""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith(f"## {section_name}"):
            # Find the next section or end
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## ") and not lines[j].startswith("---"):
                j += 1
            # Insert before the next section
            lines.insert(j, new_content)
            break
    
    return '\n'.join(lines)


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
