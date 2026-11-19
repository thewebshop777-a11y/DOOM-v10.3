"""
DOOM AI — Composio action library (expanded)
"""
from fastapi import APIRouter
from typing import Dict, List

router = APIRouter()

ACTION_LIBRARY: Dict[str, List[dict]] = {
    "slack": [
        {"id": "chat.postMessage", "name": "Post Message", "params": ["channel", "text"]},
        {"id": "chat.update", "name": "Update Message", "params": ["channel", "ts", "text"]},
        {"id": "conversations.list", "name": "List Channels", "params": []},
        {"id": "reactions.add", "name": "Add Reaction", "params": ["channel", "timestamp", "name"]},
        {"id": "files.upload", "name": "Upload File", "params": ["channels", "content", "filename"]},
    ],
    "notion": [
        {"id": "pages.create", "name": "Create Page", "params": ["parent", "title", "content"]},
        {"id": "pages.update", "name": "Update Page", "params": ["page_id", "content"]},
        {"id": "databases.query", "name": "Query Database", "params": ["database_id"]},
        {"id": "blocks.append", "name": "Append Blocks", "params": ["block_id", "children"]},
        {"id": "comments.create", "name": "Add Comment", "params": ["page_id", "text"]},
    ],
    "github": [
        {"id": "issues.create", "name": "Create Issue", "params": ["repo", "title", "body"]},
        {"id": "pulls.create", "name": "Create PR", "params": ["repo", "title", "head", "base"]},
        {"id": "repos.list", "name": "List Repos", "params": []},
        {"id": "actions.workflow_dispatch", "name": "Trigger Workflow", "params": ["repo", "workflow_id", "ref"]},
        {"id": "comments.create", "name": "Comment on Issue/PR", "params": ["repo", "issue_number", "body"]},
    ],
    "outlook": [
        {"id": "messages.send", "name": "Send Email", "params": ["to", "subject", "body"]},
        {"id": "messages.list", "name": "List Messages", "params": ["folder"]},
        {"id": "calendar.create", "name": "Create Event", "params": ["subject", "start", "end"]},
    ],
    "teams": [
        {"id": "chat.send", "name": "Send Chat", "params": ["chat_id", "content"]},
        {"id": "channels.list", "name": "List Channels", "params": ["team_id"]},
    ],
    "google-sheets": [
        {"id": "values.append", "name": "Append Row", "params": ["spreadsheet_id", "range", "values"]},
        {"id": "values.get", "name": "Get Values", "params": ["spreadsheet_id", "range"]},
        {"id": "values.update", "name": "Update Values", "params": ["spreadsheet_id", "range", "values"]},
    ],
    "google-docs": [
        {"id": "documents.create", "name": "Create Doc", "params": ["title"]},
        {"id": "documents.batchUpdate", "name": "Update Doc", "params": ["document_id", "requests"]},
    ],
    "google-drive": [
        {"id": "files.create", "name": "Upload File", "params": ["name", "content"]},
        {"id": "files.list", "name": "List Files", "params": ["q"]},
        {"id": "permissions.create", "name": "Share File", "params": ["file_id", "email", "role"]},
    ],
    "hubspot": [
        {"id": "contacts.create", "name": "Create Contact", "params": ["email", "firstname", "lastname"]},
        {"id": "deals.create", "name": "Create Deal", "params": ["dealname", "amount"]},
        {"id": "engagements.create", "name": "Log Engagement", "params": ["type", "contact_id"]},
    ],
    "salesforce": [
        {"id": "sobjects.Account.create", "name": "Create Account", "params": ["Name"]},
        {"id": "sobjects.Contact.create", "name": "Create Contact", "params": ["LastName", "Email"]},
        {"id": "query", "name": "SOQL Query", "params": ["q"]},
    ],
    "linear": [
        {"id": "issues.create", "name": "Create Issue", "params": ["title", "description", "team"]},
        {"id": "issues.update", "name": "Update Issue", "params": ["id", "state"]},
        {"id": "comments.create", "name": "Add Comment", "params": ["issue_id", "body"]},
    ],
    "jira": [
        {"id": "issues.create", "name": "Create Issue", "params": ["project", "summary", "description"]},
        {"id": "issues.transition", "name": "Transition Issue", "params": ["issue_key", "transition"]},
        {"id": "comments.add", "name": "Add Comment", "params": ["issue_key", "body"]},
    ],
    "asana": [
        {"id": "tasks.create", "name": "Create Task", "params": ["name", "notes", "project"]},
        {"id": "tasks.update", "name": "Update Task", "params": ["task_id", "completed"]},
        {"id": "projects.list", "name": "List Projects", "params": []},
    ],
    "airtable": [
        {"id": "records.create", "name": "Create Record", "params": ["base_id", "table", "fields"]},
        {"id": "records.list", "name": "List Records", "params": ["base_id", "table"]},
        {"id": "records.update", "name": "Update Record", "params": ["base_id", "table", "record_id", "fields"]},
    ],
    "vercel": [
        {"id": "deployments.create", "name": "Create Deployment", "params": ["project", "ref"]},
        {"id": "deployments.list", "name": "List Deployments", "params": ["project"]},
    ],
    "canva": [
        {"id": "designs.create", "name": "Create Design", "params": ["type", "title"]},
        {"id": "exports.create", "name": "Export Design", "params": ["design_id", "format"]},
    ],
    "figma": [
        {"id": "files.get", "name": "Get File", "params": ["file_key"]},
        {"id": "comments.post", "name": "Post Comment", "params": ["file_key", "message"]},
    ],
    "linkedin": [
        {"id": "ugcPosts.create", "name": "Create Post", "params": ["text", "visibility"]},
        {"id": "shares.create", "name": "Share Update", "params": ["text"]},
    ],
    "youtube": [
        {"id": "videos.insert", "name": "Upload Video", "params": ["title", "description"]},
        {"id": "search.list", "name": "Search Videos", "params": ["q"]},
    ],
    "intercom": [
        {"id": "messages.create", "name": "Send Message", "params": ["from", "to", "body"]},
        {"id": "conversations.reply", "name": "Reply to Conversation", "params": ["conversation_id", "body"]},
    ],
    "zendesk": [
        {"id": "tickets.create", "name": "Create Ticket", "params": ["subject", "comment"]},
        {"id": "tickets.update", "name": "Update Ticket", "params": ["ticket_id", "status"]},
    ],
}

@router.get("/{connector_id}")
async def get_actions(connector_id: str):
    actions = ACTION_LIBRARY.get(connector_id, [])
    return {"connector": connector_id, "actions": actions, "count": len(actions)}

@router.get("/")
async def list_all():
    return {"library": ACTION_LIBRARY, "apps": list(ACTION_LIBRARY.keys())}
