---
name: done-ticket
description: Marks Real Estate Project tickets as complete and moves them to done directory in Obsidian vault. Use when a ticket mission is complete or user asks to mark a ticket as done.
---

# Obsidian Done Ticket Handler

Marks engineering tickets as complete and archives them to the done directory. Updates status and completion metadata for the Real Estate Project.

## Prerequisites

**Before marking tickets done**, check for Obsidian MCP server:

1. List available MCP servers to confirm `user-obsidian-tickets` MCP is available
2. The server provides: `read_ticket`, `update_ticket`, `move_ticket` tools
3. If MCP not available, inform user and provide instructions only

## Output Rules (Strict)

**Mode 1: MCP Available**
- Pass `project: "Real Estate Project"` (exact Obsidian folder name) to all tool calls
- The server resolves the path dynamically — no hardcoded paths needed
- If unsure of the exact folder name, call `list_projects` first
- Use `read_ticket`, `update_ticket`, and `move_ticket` in sequence
- Preserve original filename; confirm completion with user

**Mode 2: No MCP**
- Output instructions for manual completion
- Show updated frontmatter user should apply
- No conversation, explanations, or commentary beyond essentials

## Completion Requirements

- **Status Update**: Change status to `✅ Done`
- **Completion Date**: Add `completed: YYYY-MM-DD` to frontmatter
- **Archive Location**: Move to `done/` subdirectory
- **Filename**: Keep original filename unchanged
- **Preserve Content**: Keep all ticket content intact

## Workflow

1. **Identify Ticket**
   - Get ticket filename from user or context
   - If not specified, list recent tickets and ask user to confirm

2. **Read Current Ticket**
   - Use `read_ticket` MCP tool to read the ticket
   - Verify it exists and is in To Do/In Progress state

3. **Update Status**
   - Use `update_ticket` MCP tool with `status: "done"`
   - Add completion notes using the `notes` parameter
   - Example: `update_ticket(filename="TICKET-XXX.md", status="done", notes="Completed [description]")`

4. **Move to Done**
   - Use `move_ticket` MCP tool to move ticket to `done/` subdirectory
   - Example: `move_ticket(filename="TICKET-XXX.md")`
   - The tool automatically creates the done directory if needed
   - Keeps original filename

5. **Confirm**
   - Brief confirmation: "Ticket {{FILENAME}} marked as done and moved to done/"
   - No additional commentary

## Example Frontmatter Transformation

**Before:**
```yaml
---
created: 2026-02-01
status: 📝 To Do
tags: [ticket, backend]
priority: P2-Medium
---
```

**After:**
```yaml
---
created: 2026-02-01
status: ✅ Done
completed: 2026-02-02
tags: [ticket, backend]
priority: P2-Medium
---
```

## Error Handling

- **Ticket Not Found**: List available tickets and ask user to specify
- **Already Done**: Check if ticket is already in done/ and inform user
- **Permission Issues**: Inform user and provide manual instructions
- **MCP Unavailable**: Provide clear manual instructions

## Scope

**This skill is for Real Estate Project tickets only.**
- Target vault: `/Users/danielmo/Desktop/Daniel/Real Estate Project/`
- Only operates on tickets in this project directory
- Does not affect other Obsidian notes or projects

## Notes

- Tickets retain all original metadata and content
- Done tickets can be referenced by their original filename
- The done/ directory serves as an archive of completed work
- Status changes are permanent (tickets don't move back to active)
