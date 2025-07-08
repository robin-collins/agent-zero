## Tool: calendar_manager

**Description**: Comprehensive calendar management tool for CalDAV protocol integration. Supports calendar operations including creating events, listing events, updating events, deleting events, and managing multiple calendars with robust error handling, timezone support, and search capabilities.

**Important**: 
- Always provide clear, descriptive titles for calendar events
- Use ISO format for dates and times (YYYY-MM-DDTHH:MM:SS)
- When timezone is not specified, UTC is assumed
- For all-day events, set "all_day": true and use date format without time
- Event IDs are returned after creation and needed for updates/deletions

**Configuration**: Calendar settings are loaded from environment variables in the .env file. Required variables:
- `CALDAV_URL`: CalDAV server URL (e.g., https://calendar.example.com/caldav/)
- `CALDAV_USERNAME`: Calendar account username
- `CALDAV_PASSWORD`: Calendar account password

Optional variables:
- `CALDAV_DEFAULT_CALENDAR`: Default calendar name (defaults to "Agent Zero Calendar")
- `CALDAV_TIMEZONE`: Default timezone for events (defaults to "UTC")

**Methods Available**:

### list_calendars
List all available calendars on the CalDAV server.

**Usage**:
```json
{
    "thoughts": ["I need to see what calendars are available"],
    "headline": "Listing available calendars",
    "tool_name": "calendar_manager:list_calendars",
    "tool_args": {}
}
```

**Returns**: JSON with calendar list including names, URLs, and metadata.

### list_events
List events in a specified date range from a calendar.

**Usage**:
```json
{
    "tool_name": "calendar_manager:list_events",
    "tool_args": {
        "calendar_name": "Work Calendar",
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-31T23:59:59",
        "max_events": 50
    }
}
```

**Parameters**:
- `calendar_name` (optional): Calendar name, defaults to default calendar
- `start_date` (optional): Start date in ISO format, defaults to today
- `end_date` (optional): End date in ISO format, defaults to 30 days from start
- `max_events` (optional): Maximum events to return, defaults to 50

### create_event
Create a new calendar event.

**Usage**:
```json
{
    "thoughts": ["I need to create a new meeting event"],
    "headline": "Creating team meeting event",
    "tool_name": "calendar_manager:create_event",
    "tool_args": {
        "title": "Team Meeting",
        "start_datetime": "2024-01-15T14:00:00",
        "end_datetime": "2024-01-15T15:00:00",
        "description": "Weekly team sync meeting",
        "location": "Conference Room A",
        "calendar_name": "Work Calendar",
        "all_day": false,
        "timezone_name": "America/New_York"
    }
}
```

**Parameters**:
- `title` (required): Event title/summary
- `start_datetime` (required): Start date and time in ISO format
- `end_datetime` (optional): End date and time, defaults to 1 hour after start
- `description` (optional): Event description/notes
- `location` (optional): Event location
- `calendar_name` (optional): Target calendar name
- `all_day` (optional): Whether this is an all-day event, defaults to false
- `timezone_name` (optional): Timezone for the event, defaults to server default

### get_event
Retrieve a specific event by ID.

**Usage**:
```json
{
    "tool_name": "calendar_manager:get_event",
    "tool_args": {
        "event_id": "agent-zero-1642234567.123@agent-zero",
        "calendar_name": "Work Calendar"
    }
}
```

**Parameters**:
- `event_id` (required): Event UID or ID
- `calendar_name` (optional): Calendar containing the event

### update_event
Update an existing calendar event.

**Usage**:
```json
{
    "tool_name": "calendar_manager:update_event",
    "tool_args": {
        "event_id": "agent-zero-1642234567.123@agent-zero",
        "title": "Updated Team Meeting",
        "start_datetime": "2024-01-15T15:00:00",
        "end_datetime": "2024-01-15T16:00:00",
        "description": "Rescheduled team sync meeting",
        "location": "Conference Room B",
        "calendar_name": "Work Calendar"
    }
}
```

**Parameters**:
- `event_id` (required): Event UID or ID to update
- `title` (optional): New event title
- `start_datetime` (optional): New start date and time
- `end_datetime` (optional): New end date and time
- `description` (optional): New description
- `location` (optional): New location
- `calendar_name` (optional): Calendar containing the event

### delete_event
Delete a calendar event by ID.

**Usage**:
```json
{
    "tool_name": "calendar_manager:delete_event",
    "tool_args": {
        "event_id": "agent-zero-1642234567.123@agent-zero",
        "calendar_name": "Work Calendar"
    }
}
```

**Parameters**:
- `event_id` (required): Event UID or ID to delete
- `calendar_name` (optional): Calendar containing the event

### search_events
Search for events by text query across titles, descriptions, and locations.

**Usage**:
```json
{
    "tool_name": "calendar_manager:search_events",
    "tool_args": {
        "query": "team meeting",
        "calendar_name": "Work Calendar",
        "max_results": 20
    }
}
```

**Parameters**:
- `query` (required): Text to search for in events
- `calendar_name` (optional): Calendar to search in
- `max_results` (optional): Maximum results to return, defaults to 20

**Response Format**: All methods return JSON responses with operation results, including status information, event details, and relevant metadata. Dates and times are returned in ISO format.

**Error Handling**: The tool provides comprehensive error handling for connection issues, authentication failures, invalid event IDs, missing calendars, and timezone errors. All errors are logged and returned as descriptive messages.

**Examples**:

Create a simple meeting:
```json
{
    "thoughts": ["User needs to schedule a doctor appointment"],
    "headline": "Creating doctor appointment",
    "tool_name": "calendar_manager:create_event",
    "tool_args": {
        "title": "Doctor Appointment",
        "start_datetime": "2024-01-20T10:00:00",
        "end_datetime": "2024-01-20T11:00:00"
    }
}
```

List upcoming events:
```json
{
    "thoughts": ["I should check what events are coming up"],
    "headline": "Checking upcoming events",
    "tool_name": "calendar_manager:list_events",
    "tool_args": {
        "start_date": "2024-01-01T00:00:00",
        "max_events": 10
    }
}
```

Search for work meetings:
```json
{
    "thoughts": ["I need to find all work-related meetings"],
    "headline": "Searching for work meetings",
    "tool_name": "calendar_manager:search_events",
    "tool_args": {
        "query": "work meeting"
    }
}
```

Create an all-day event:
```json
{
    "thoughts": ["User wants to mark a full vacation day"],
    "headline": "Creating all-day vacation event",
    "tool_name": "calendar_manager:create_event",
    "tool_args": {
        "title": "Vacation Day",
        "start_datetime": "2024-02-15T00:00:00",
        "all_day": true,
        "description": "Personal vacation day"
    }
}
```

**Timezone Support**: The tool supports full timezone handling. Events can be created in specific timezones, and the server will handle conversion as needed. Use standard timezone names like "America/New_York", "Europe/London", "Asia/Tokyo".

**Calendar Management**: The tool can work with multiple calendars. If a calendar doesn't exist and you're using the default calendar name, it will be created automatically. For other calendar names, they must exist on the server.

**Security Notes**: 
- CalDAV credentials are stored securely in environment variables
- All connections use HTTPS encryption when properly configured
- Event IDs are generated with unique timestamps to prevent conflicts
- Connection cleanup is automatically handled after each operation

**Dependencies**: This tool requires the `caldav`, `icalendar`, and `pytz` Python packages to be installed for proper CalDAV protocol support and timezone handling.