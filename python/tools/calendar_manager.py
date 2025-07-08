from caldav import DAVClient, Calendar, Event
from icalendar import Calendar as iCalendar, Event as iEvent
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
import json
import pytz
from dataclasses import dataclass
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers import dotenv


@dataclass
class CalDAVConfig:
    """CalDAV configuration from environment variables."""

    url: str
    username: str
    password: str
    default_calendar: str
    timezone: str


class CalendarConnection:
    """Manages CalDAV connections with proper cleanup."""

    def __init__(self, config: CalDAVConfig):
        self.config = config
        self.client: Optional[DAVClient] = None
        self.principal = None
        self.calendars = {}

    async def connect(self) -> DAVClient:
        """Establish CalDAV connection."""
        try:
            self.client = DAVClient(
                url=self.config.url,
                username=self.config.username,
                password=self.config.password,
            )

            # Get principal (user account)
            self.principal = self.client.principal()

            return self.client
        except Exception as e:
            raise Exception(f"CalDAV connection failed: {str(e)}")

    async def get_calendar(self, calendar_name: Optional[str] = None) -> Calendar:
        """Get calendar by name or default calendar."""
        if not self.principal:
            await self.connect()

        calendar_name = calendar_name or self.config.default_calendar

        # Cache calendars to avoid repeated lookups
        if calendar_name not in self.calendars:
            calendars = self.principal.calendars()

            for cal in calendars:
                cal_name = cal.get_display_name() or str(cal.name)
                if cal_name == calendar_name:
                    self.calendars[calendar_name] = cal
                    break
            else:
                # Calendar not found, try to create it if it's the default
                if calendar_name == self.config.default_calendar:
                    cal = self.principal.make_calendar(name=calendar_name)
                    self.calendars[calendar_name] = cal
                else:
                    raise Exception(f"Calendar '{calendar_name}' not found")

        return self.calendars[calendar_name]

    def cleanup(self):
        """Clean up connections."""
        self.client = None
        self.principal = None
        self.calendars.clear()

    def __del__(self):
        self.cleanup()


class CalendarManager(Tool):
    """
    Comprehensive calendar management tool for Agent Zero using CalDAV protocol.

    Supports calendar operations like creating events, listing events, updating events,
    deleting events, and managing multiple calendars with robust error handling
    and timezone support.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = self._load_config()
        self.connection: Optional[CalendarConnection] = None

    def _load_config(self) -> CalDAVConfig:
        """Load CalDAV configuration from environment variables."""
        try:
            return CalDAVConfig(
                url=dotenv.get_dotenv_value("CALDAV_URL") or "",
                username=dotenv.get_dotenv_value("CALDAV_USERNAME") or "",
                password=dotenv.get_dotenv_value("CALDAV_PASSWORD") or "",
                default_calendar=dotenv.get_dotenv_value("CALDAV_DEFAULT_CALENDAR")
                or "Agent Zero Calendar",
                timezone=dotenv.get_dotenv_value("CALDAV_TIMEZONE") or "UTC",
            )
        except Exception as e:
            raise Exception(f"Failed to load CalDAV configuration: {str(e)}")

    def _validate_config(self) -> None:
        """Validate CalDAV configuration."""
        required_fields = [
            ("CalDAV URL", self.config.url),
            ("Username", self.config.username),
            ("Password", self.config.password),
        ]

        missing = [name for name, value in required_fields if not value]
        if missing:
            raise Exception(
                f"Missing required CalDAV configuration: {', '.join(missing)}"
            )

    async def execute(self, **kwargs) -> Response:
        """
        Execute calendar operations based on method.

        Supported methods:
        - list_calendars: List available calendars
        - list_events: List events in date range
        - create_event: Create new calendar event
        - get_event: Get specific event details
        - update_event: Update existing event
        - delete_event: Delete event
        - search_events: Search events by text
        """
        try:
            self._validate_config()
            self.connection = CalendarConnection(self.config)

            if self.method == "list_calendars":
                return await self.list_calendars(**kwargs)
            elif self.method == "list_events":
                return await self.list_events(**kwargs)
            elif self.method == "create_event":
                return await self.create_event(**kwargs)
            elif self.method == "get_event":
                return await self.get_event(**kwargs)
            elif self.method == "update_event":
                return await self.update_event(**kwargs)
            elif self.method == "delete_event":
                return await self.delete_event(**kwargs)
            elif self.method == "search_events":
                return await self.search_events(**kwargs)
            else:
                return Response(
                    message=f"Unknown calendar method: {self.method}. Supported methods: list_calendars, list_events, create_event, get_event, update_event, delete_event, search_events",
                    break_loop=False,
                )

        except Exception as e:
            error_msg = f"Calendar operation failed: {str(e)}"
            PrintStyle().error(error_msg)
            return Response(message=error_msg, break_loop=False)
        finally:
            if self.connection:
                self.connection.cleanup()

    async def list_calendars(self) -> Response:
        """List all available calendars."""
        try:
            self.log.update(progress="Connecting to CalDAV server...")
            await self.connection.connect()

            self.log.update(progress="Fetching calendars...")
            calendars = self.connection.principal.calendars()

            calendar_list = []
            for cal in calendars:
                cal_info = {
                    "name": cal.get_display_name() or str(cal.name),
                    "url": str(cal.url),
                    "color": getattr(cal, "color", None),
                    "description": getattr(cal, "description", None),
                }
                calendar_list.append(cal_info)

            result = {
                "calendars": calendar_list,
                "count": len(calendar_list),
                "default_calendar": self.config.default_calendar,
            }

            self.log.update(progress=f"Found {len(calendar_list)} calendars")
            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"List calendars failed: {str(e)}")

    async def list_events(
        self,
        calendar_name: str = "",
        start_date: str = "",
        end_date: str = "",
        max_events: int = 50,
    ) -> Response:
        """List events in specified date range."""
        try:
            self.log.update(progress="Connecting to CalDAV server...")
            calendar = await self.connection.get_calendar(calendar_name)

            # Parse date range
            tz = pytz.timezone(self.config.timezone)

            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            else:
                start_dt = datetime.now(tz).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = start_dt + timedelta(days=30)  # Default 30 days

            self.log.update(
                progress=f"Searching events from {start_dt.date()} to {end_dt.date()}..."
            )

            # Search for events
            events = calendar.search(
                start=start_dt, end=end_dt, event=True, expand=True
            )

            event_list = []
            for event in events[:max_events]:
                try:
                    event_data = self._extract_event_data(event)
                    event_list.append(event_data)
                except Exception as e:
                    PrintStyle().warning(f"Failed to parse event: {str(e)}")
                    continue

            result = {
                "calendar": calendar.get_display_name() or "Unknown",
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "events": event_list,
                "count": len(event_list),
                "total_found": len(events),
            }

            self.log.update(progress=f"Found {len(event_list)} events")
            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"List events failed: {str(e)}")

    async def create_event(
        self,
        title: str,
        start_datetime: str,
        end_datetime: str = "",
        description: str = "",
        location: str = "",
        calendar_name: str = "",
        all_day: bool = False,
        timezone_name: str = "",
    ) -> Response:
        """Create new calendar event."""
        try:
            if not title:
                return Response(message="Event title is required", break_loop=False)

            self.log.update(progress="Connecting to CalDAV server...")
            calendar = await self.connection.get_calendar(calendar_name)

            # Parse timezone
            tz = pytz.timezone(timezone_name or self.config.timezone)

            # Parse start datetime
            start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
            if start_dt.tzinfo is None:
                start_dt = tz.localize(start_dt)

            # Parse end datetime
            if end_datetime:
                end_dt = datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))
                if end_dt.tzinfo is None:
                    end_dt = tz.localize(end_dt)
            else:
                # Default to 1 hour duration
                end_dt = start_dt + timedelta(hours=1)

            self.log.update(progress="Creating event...")

            # Create iCalendar event
            cal = iCalendar()
            event = iEvent()

            event.add("uid", f"agent-zero-{datetime.now().timestamp()}@agent-zero")
            event.add("dtstart", start_dt)
            event.add("dtend", end_dt)
            event.add("summary", title)
            event.add("created", datetime.now(timezone.utc))
            event.add("dtstamp", datetime.now(timezone.utc))

            if description:
                event.add("description", description)
            if location:
                event.add("location", location)

            if all_day:
                event.add("dtstart", start_dt.date())
                event.add("dtend", end_dt.date())

            cal.add_component(event)

            # Save to calendar
            calendar.save_event(cal.to_ical().decode("utf-8"))

            result = {
                "status": "created",
                "title": title,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "calendar": calendar.get_display_name() or "Unknown",
                "all_day": all_day,
                "location": location,
                "description": description,
            }

            self.log.update(progress="Event created successfully")
            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"Create event failed: {str(e)}")

    async def get_event(self, event_id: str, calendar_name: str = "") -> Response:
        """Get specific event by ID."""
        try:
            self.log.update(progress="Connecting to CalDAV server...")
            calendar = await self.connection.get_calendar(calendar_name)

            self.log.update(progress=f"Searching for event: {event_id}")

            # Search for event by UID
            events = calendar.search(event=True, expand=True)

            for event in events:
                try:
                    event_data = self._extract_event_data(event)
                    if (
                        event_data.get("uid") == event_id
                        or event_data.get("id") == event_id
                    ):
                        self.log.update(progress="Event found")
                        return Response(
                            message=json.dumps(event_data, indent=2), break_loop=False
                        )
                except Exception:
                    continue

            return Response(
                message=f"Event with ID '{event_id}' not found", break_loop=False
            )

        except Exception as e:
            raise Exception(f"Get event failed: {str(e)}")

    async def update_event(
        self,
        event_id: str,
        title: str = "",
        start_datetime: str = "",
        end_datetime: str = "",
        description: str = "",
        location: str = "",
        calendar_name: str = "",
    ) -> Response:
        """Update existing event."""
        try:
            self.log.update(progress="Connecting to CalDAV server...")
            calendar = await self.connection.get_calendar(calendar_name)

            self.log.update(progress=f"Finding event: {event_id}")

            # Find the event
            events = calendar.search(event=True, expand=True)
            target_event = None

            for event in events:
                try:
                    event_data = self._extract_event_data(event)
                    if (
                        event_data.get("uid") == event_id
                        or event_data.get("id") == event_id
                    ):
                        target_event = event
                        break
                except Exception:
                    continue

            if not target_event:
                return Response(
                    message=f"Event with ID '{event_id}' not found", break_loop=False
                )

            self.log.update(progress="Updating event...")

            # Parse existing event
            cal_data = target_event.vobject_instance.vevent

            # Update fields if provided
            if title:
                cal_data.summary.value = title
            if start_datetime:
                tz = pytz.timezone(self.config.timezone)
                start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = tz.localize(start_dt)
                cal_data.dtstart.value = start_dt
            if end_datetime:
                tz = pytz.timezone(self.config.timezone)
                end_dt = datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))
                if end_dt.tzinfo is None:
                    end_dt = tz.localize(end_dt)
                cal_data.dtend.value = end_dt
            if description:
                if hasattr(cal_data, "description"):
                    cal_data.description.value = description
                else:
                    cal_data.add("description").value = description
            if location:
                if hasattr(cal_data, "location"):
                    cal_data.location.value = location
                else:
                    cal_data.add("location").value = location

            # Save updated event
            target_event.save()

            result = {
                "status": "updated",
                "event_id": event_id,
                "calendar": calendar.get_display_name() or "Unknown",
            }

            self.log.update(progress="Event updated successfully")
            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"Update event failed: {str(e)}")

    async def delete_event(self, event_id: str, calendar_name: str = "") -> Response:
        """Delete event by ID."""
        try:
            self.log.update(progress="Connecting to CalDAV server...")
            calendar = await self.connection.get_calendar(calendar_name)

            self.log.update(progress=f"Finding event: {event_id}")

            # Find the event
            events = calendar.search(event=True, expand=True)

            for event in events:
                try:
                    event_data = self._extract_event_data(event)
                    if (
                        event_data.get("uid") == event_id
                        or event_data.get("id") == event_id
                    ):
                        self.log.update(progress="Deleting event...")
                        event.delete()

                        result = {
                            "status": "deleted",
                            "event_id": event_id,
                            "title": event_data.get("title", "Unknown"),
                            "calendar": calendar.get_display_name() or "Unknown",
                        }

                        self.log.update(progress="Event deleted successfully")
                        return Response(
                            message=json.dumps(result, indent=2), break_loop=False
                        )
                except Exception:
                    continue

            return Response(
                message=f"Event with ID '{event_id}' not found", break_loop=False
            )

        except Exception as e:
            raise Exception(f"Delete event failed: {str(e)}")

    async def search_events(
        self, query: str, calendar_name: str = "", max_results: int = 20
    ) -> Response:
        """Search events by text query."""
        try:
            self.log.update(progress="Connecting to CalDAV server...")
            calendar = await self.connection.get_calendar(calendar_name)

            self.log.update(progress=f"Searching for: {query}")

            # Get all events and filter by text search
            events = calendar.search(event=True, expand=True)

            matching_events = []
            query_lower = query.lower()

            for event in events:
                try:
                    event_data = self._extract_event_data(event)

                    # Search in title, description, and location
                    searchable_text = " ".join(
                        [
                            event_data.get("title", ""),
                            event_data.get("description", ""),
                            event_data.get("location", ""),
                        ]
                    ).lower()

                    if query_lower in searchable_text:
                        matching_events.append(event_data)

                        if len(matching_events) >= max_results:
                            break

                except Exception:
                    continue

            result = {
                "query": query,
                "calendar": calendar.get_display_name() or "Unknown",
                "events": matching_events,
                "count": len(matching_events),
            }

            self.log.update(progress=f"Found {len(matching_events)} matching events")
            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"Search events failed: {str(e)}")

    def _extract_event_data(self, event: Event) -> Dict[str, Any]:
        """Extract event data from CalDAV event object."""
        try:
            vobject = event.vobject_instance
            vevent = vobject.vevent

            data = {
                "id": str(event.url).split("/")[-1],
                "uid": getattr(vevent, "uid", {}).value
                if hasattr(vevent, "uid")
                else None,
                "title": getattr(vevent, "summary", {}).value
                if hasattr(vevent, "summary")
                else "No Title",
                "description": getattr(vevent, "description", {}).value
                if hasattr(vevent, "description")
                else "",
                "location": getattr(vevent, "location", {}).value
                if hasattr(vevent, "location")
                else "",
                "url": str(event.url),
            }

            # Handle start/end times
            if hasattr(vevent, "dtstart"):
                start_dt = vevent.dtstart.value
                if isinstance(start_dt, datetime):
                    data["start"] = start_dt.isoformat()
                    data["all_day"] = False
                else:
                    # Date only (all-day event)
                    data["start"] = start_dt.isoformat()
                    data["all_day"] = True

            if hasattr(vevent, "dtend"):
                end_dt = vevent.dtend.value
                if isinstance(end_dt, datetime):
                    data["end"] = end_dt.isoformat()
                else:
                    data["end"] = end_dt.isoformat()

            # Additional properties
            if hasattr(vevent, "created"):
                data["created"] = vevent.created.value.isoformat()
            if hasattr(vevent, "last_modified"):
                data["modified"] = vevent.last_modified.value.isoformat()
            if hasattr(vevent, "status"):
                data["status"] = vevent.status.value

            return data

        except Exception as e:
            raise Exception(f"Failed to extract event data: {str(e)}")

    def get_log_object(self):
        """Create custom log object for calendar operations."""
        method_icons = {
            "list_calendars": "calendar_view_month",
            "list_events": "event",
            "create_event": "event_note",
            "get_event": "event_available",
            "update_event": "edit_calendar",
            "delete_event": "event_busy",
            "search_events": "search",
        }

        icon = method_icons.get(self.method, "calendar_today")
        method_name = self.method or "calendar_operation"

        return self.agent.context.log.log(
            type="calendar",
            heading=f"icon://{icon} {self.agent.agent_name}: Calendar {method_name.replace('_', ' ').title()}",
            content="",
            kvps=self.args,
        )

    async def before_execution(self, **kwargs):
        """Custom pre-execution setup."""
        await super().before_execution(**kwargs)
        self.log.update(progress="Initializing calendar operation...")

    async def after_execution(self, response: Response, **kwargs):
        """Custom post-execution cleanup."""
        if self.connection:
            self.connection.cleanup()
        await super().after_execution(response, **kwargs)
