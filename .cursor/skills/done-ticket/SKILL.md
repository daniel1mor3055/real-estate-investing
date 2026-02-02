---
name: done-ticket
description: Marks Real Estate Project tickets as complete and moves them to done directory in Obsidian vault. Use when a ticket mission is complete or user asks to mark a ticket as done.
---

# Obsidian Done Ticket Handler

Marks engineering tickets as complete and archives them to the done directory. Updates status and completion metadata for the Real Estate Project.

## Prerequisites

**Before marking tickets done**, check for Obsidian MCP server:

1. List available MCP servers to confirm `obsidian` or similar MCP is available
2. Read the Obsidian MCP tool descriptors to understand available operations (likely `read_note`, `write_note`, `move_note`, or similar)
3. If MCP not available, inform user and provide instructions only

## Output Rules (Strict)

**Mode 1: MCP Available**
- Read the current ticket content from `/Users/danielmo/Desktop/Daniel/Real Estate Project/`
- Update frontmatter: set status to `✅ Done` and add `completed: YYYY-MM-DD`
- Move ticket to `/Users/danielmo/Desktop/Daniel/Real Estate Project/done/`
- Preserve original filename
- Confirm completion with user

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
   - Use Obsidian MCP to read the ticket
   - Verify it exists and is in To Do/In Progress state

3. **Update Frontmatter**
   - Change `status: 📝 To Do` or `status: 🔄 In Progress` to `status: ✅ Done`
   - Add `completed: {{TODAY_YYYY-MM-DD}}` field
   - Preserve all other frontmatter fields

4. **Move to Done**
   - Move ticket to `done/` subdirectory
   - Ensure done directory exists (create if needed)
   - Keep original filename

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
