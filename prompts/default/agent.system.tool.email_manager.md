## Tool: email_manager

**Description**: Comprehensive email management tool for IMAP mailbox operations and SMTP email sending. Supports checking inbox, reading emails, sending new emails (both plain text and HTML formatted), replying to emails, and managing IMAP folders with robust error handling and progress tracking.

**Important**: 
- Always provide clear, descriptive subjects for outgoing emails
- Email IDs are returned from check_inbox and needed for read/reply/move operations
- Use proper email addresses with valid format (user@domain.com)
- Attachments must be valid file paths that exist on the system
- Supports both plain text and HTML email formats (use "format" parameter)

**Configuration**: Email settings are loaded from environment variables in the .env file. Required variables:
- `EMAIL_IMAP_HOST`: IMAP server hostname
- `EMAIL_SMTP_HOST`: SMTP server hostname  
- `EMAIL_USERNAME`: Email account username
- `EMAIL_PASSWORD`: Email account password

Optional variables:
- `EMAIL_IMAP_PORT`: IMAP port (defaults to 993)
- `EMAIL_SMTP_PORT`: SMTP port (defaults to 587)
- `EMAIL_IMAP_USE_SSL`: Use SSL for IMAP (defaults to true)
- `EMAIL_SMTP_USE_TLS`: Use TLS for SMTP (defaults to true)
- `EMAIL_FROM_NAME`: Display name for sent emails (defaults to "Agent Zero")

**Methods Available**:

### check_inbox
Check for emails in a specific folder with given status.

**Usage**:
```json
{
    "thoughts": ["I need to check for new unread emails"],
    "headline": "Checking inbox for unread emails",
    "tool_name": "email_manager:check_inbox",
    "tool_args": {
        "folder": "INBOX",
        "status": "UNSEEN"
    }
}
```

**Parameters**:
- `folder` (optional): IMAP folder name, defaults to "INBOX"
- `status` (optional): Email status to search for, defaults to "UNSEEN" (unread)

### read_email  
Read a specific email by ID from a folder.

**Usage**:
```json
{
    "tool_name": "email_manager:read_email", 
    "tool_args": {
        "email_id": "123",
        "folder": "INBOX"
    }
}
```

**Parameters**:
- `email_id` (required): Email ID to read
- `folder` (optional): Folder containing the email, defaults to "INBOX"

### send_email
Send a new email with optional attachments.

**Usage**:
```json
{
    "thoughts": ["I need to send an email with the requested information"],
    "headline": "Sending email to recipient",
    "tool_name": "email_manager:send_email",
    "tool_args": {
        "to": "recipient@example.com",
        "subject": "Email Subject",
        "body": "Email content here",
        "cc": "cc@example.com",
        "bcc": "bcc@example.com",
        "attachments": ["/path/to/file1.pdf", "/path/to/file2.txt"],
        "format": "plain"
    }
}
```

**Parameters**:
- `to` (required): Primary recipient email address
- `subject` (required): Email subject line
- `body` (required): Email body content
- `cc` (optional): Carbon copy recipients (comma-separated)
- `bcc` (optional): Blind carbon copy recipients (comma-separated)
- `attachments` (optional): List of file paths to attach
- `format` (optional): Email format - "plain" for plain text or "html" for HTML, defaults to "plain"

### reply_email
Reply to an existing email by ID.

**Usage**:
```json
{
    "tool_name": "email_manager:reply_email",
    "tool_args": {
        "email_id": "123", 
        "body": "Reply message content",
        "folder": "INBOX",
        "reply_all": false
    }
}
```

**Parameters**:
- `email_id` (required): ID of email to reply to
- `body` (required): Reply message content
- `folder` (optional): Folder containing original email, defaults to "INBOX"
- `reply_all` (optional): Whether to reply to all recipients, defaults to false

### list_folders
List all available IMAP folders.

**Usage**:
```json
{
    "thoughts": ["I need to see what email folders are available"],
    "headline": "Listing email folders",
    "tool_name": "email_manager:list_folders",
    "tool_args": {}
}
```

### mark_read
Mark an email as read.

**Usage**:
```json
{
    "tool_name": "email_manager:mark_read",
    "tool_args": {
        "email_id": "123",
        "folder": "INBOX"
    }
}
```

**Parameters**:
- `email_id` (required): Email ID to mark as read
- `folder` (optional): Folder containing the email, defaults to "INBOX"

### move_email
Move an email from one folder to another.

**Usage**:
```json
{
    "tool_name": "email_manager:move_email",
    "tool_args": {
        "email_id": "123",
        "from_folder": "INBOX",
        "to_folder": "Archive"
    }
}
```

**Parameters**:
- `email_id` (required): Email ID to move
- `from_folder` (optional): Source folder, defaults to "INBOX"
- `to_folder` (required): Destination folder

**Response Format**: All methods return JSON responses with operation results, including status information, email details, and any relevant metadata.

**Error Handling**: The tool provides comprehensive error handling for connection issues, authentication failures, invalid email IDs, and missing configuration. All errors are logged and returned as descriptive messages.

**Examples**:

Check for unread emails:
```json
{
    "thoughts": ["I should check if there are any new emails to process"],
    "headline": "Checking for unread emails",
    "tool_name": "email_manager:check_inbox",
    "tool_args": {}
}
```

Send a simple email:
```json
{
    "thoughts": ["User wants me to send a greeting email"],
    "headline": "Sending greeting email",
    "tool_name": "email_manager:send_email",
    "tool_args": {
        "to": "user@example.com",
        "subject": "Hello from Agent Zero",
        "body": "This is an automated message from Agent Zero."
    }
}
```

Read a specific email:
```json
{
    "thoughts": ["I need to read the content of this specific email"],
    "headline": "Reading email content",
    "tool_name": "email_manager:read_email",
    "tool_args": {
        "email_id": "42"
    }
}
```

Send an HTML formatted email:
```json
{
    "thoughts": ["User wants to send a formatted email with HTML styling"],
    "headline": "Sending HTML formatted email",
    "tool_name": "email_manager:send_email",
    "tool_args": {
        "to": "user@example.com",
        "subject": "Formatted Report",
        "body": "<html><body><h1>Monthly Report</h1><p>Here is your <strong>monthly report</strong> with <em>important updates</em>.</p><ul><li>Sales: $10,000</li><li>Customers: 150</li></ul></body></html>",
        "format": "html"
    }
}
```

**Security Notes**: 
- Email credentials are stored securely in environment variables
- All connections use appropriate encryption (SSL/TLS)
- Attachments are validated before processing
- Connection cleanup is automatically handled after each operation

**Dependencies**: This tool uses Python's built-in email libraries (imaplib, smtplib, email) and requires no additional packages for basic functionality.