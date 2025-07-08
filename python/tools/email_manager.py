import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, parseaddr
from typing import List, Dict, Optional, Any
import json
import os
from dataclasses import dataclass
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers import dotenv, files


@dataclass
class EmailConfig:
    """Email configuration from environment variables."""

    imap_host: str
    imap_port: int
    imap_use_ssl: bool
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    username: str
    password: str
    from_name: str


class EmailConnection:
    """Manages email connections with proper cleanup."""

    def __init__(self, config: EmailConfig):
        self.config = config
        self.imap_conn: Optional[imaplib.IMAP4_SSL] = None
        self.smtp_conn: Optional[smtplib.SMTP] = None

    async def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Establish IMAP connection."""
        try:
            if self.config.imap_use_ssl:
                self.imap_conn = imaplib.IMAP4_SSL(
                    self.config.imap_host, self.config.imap_port
                )
            else:
                self.imap_conn = imaplib.IMAP4(
                    self.config.imap_host, self.config.imap_port
                )

            self.imap_conn.login(self.config.username, self.config.password)
            return self.imap_conn
        except Exception as e:
            raise Exception(f"IMAP connection failed: {str(e)}")

    async def connect_smtp(self) -> smtplib.SMTP:
        """Establish SMTP connection."""
        try:
            self.smtp_conn = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)

            if self.config.smtp_use_tls:
                self.smtp_conn.starttls()

            self.smtp_conn.login(self.config.username, self.config.password)
            return self.smtp_conn
        except Exception as e:
            raise Exception(f"SMTP connection failed: {str(e)}")

    def cleanup(self):
        """Clean up connections."""
        if self.imap_conn:
            try:
                self.imap_conn.logout()
            except Exception:
                pass
            self.imap_conn = None

        if self.smtp_conn:
            try:
                self.smtp_conn.quit()
            except Exception:
                pass
            self.smtp_conn = None

    def __del__(self):
        self.cleanup()


class EmailManager(Tool):
    """
    Comprehensive email management tool for Agent Zero.

    Supports IMAP mailbox operations and SMTP email sending with robust
    error handling, progress tracking, and environment-based configuration.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = None
        self.connection: Optional[EmailConnection] = None
        self.is_initialized = False
        self.initialization_error = None
        
        # Initialize email configuration and test connections
        self._initialize_email_service()

    def _load_config(self) -> EmailConfig:
        """Load email configuration from environment variables."""
        try:
            return EmailConfig(
                imap_host=dotenv.get_dotenv_value("EMAIL_IMAP_HOST") or "",
                imap_port=int(dotenv.get_dotenv_value("EMAIL_IMAP_PORT") or "993"),
                imap_use_ssl=dotenv.get_dotenv_value(
                    "EMAIL_IMAP_USE_SSL", "true"
                ).lower()
                == "true",
                smtp_host=dotenv.get_dotenv_value("EMAIL_SMTP_HOST") or "",
                smtp_port=int(dotenv.get_dotenv_value("EMAIL_SMTP_PORT") or "587"),
                smtp_use_tls=dotenv.get_dotenv_value(
                    "EMAIL_SMTP_USE_TLS", "true"
                ).lower()
                == "true",
                username=dotenv.get_dotenv_value("EMAIL_USERNAME") or "",
                password=dotenv.get_dotenv_value("EMAIL_PASSWORD") or "",
                from_name=dotenv.get_dotenv_value("EMAIL_FROM_NAME") or "Agent Zero",
            )
        except Exception as e:
            raise Exception(f"Failed to load email configuration: {str(e)}")

    def _initialize_email_service(self) -> None:
        """Initialize email service with validation and connection testing."""
        try:
            # Load configuration
            self.config = self._load_config()
            
            # Validate configuration
            self._validate_config()
            
            # Test connections
            self._test_connections()
            
            self.is_initialized = True
            PrintStyle().success("Email service initialized successfully")
            
        except Exception as e:
            self.initialization_error = str(e)
            PrintStyle().error(f"Email service initialization failed: {str(e)}")
            self.is_initialized = False
    
    def _validate_config(self) -> None:
        """Validate email configuration with detailed error messages."""
        if not self.config:
            raise Exception("Email configuration could not be loaded")
            
        required_fields = [
            ("EMAIL_IMAP_HOST", self.config.imap_host),
            ("EMAIL_SMTP_HOST", self.config.smtp_host),
            ("EMAIL_USERNAME", self.config.username),
            ("EMAIL_PASSWORD", self.config.password),
        ]

        missing = [name for name, value in required_fields if not value]
        if missing:
            raise Exception(
                f"Missing required email environment variables: {', '.join(missing)}. "
                f"Please check your .env file and ensure all email configuration is set."
            )
            
        # Validate port numbers
        if not (1 <= self.config.imap_port <= 65535):
            raise Exception(f"Invalid IMAP port: {self.config.imap_port}. Must be between 1 and 65535")
            
        if not (1 <= self.config.smtp_port <= 65535):
            raise Exception(f"Invalid SMTP port: {self.config.smtp_port}. Must be between 1 and 65535")
    
    def _test_connections(self) -> None:
        """Test both IMAP and SMTP connections during initialization."""
        test_connection = EmailConnection(self.config)
        
        try:
            # Test IMAP connection
            PrintStyle().info("Testing IMAP connection...")
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                imap_conn = loop.run_until_complete(test_connection.connect_imap())
                imap_conn.logout()
                PrintStyle().success("IMAP connection test successful")
            except Exception as e:
                raise Exception(f"IMAP connection test failed: {str(e)}")
            
            # Test SMTP connection
            PrintStyle().info("Testing SMTP connection...")
            try:
                smtp_conn = loop.run_until_complete(test_connection.connect_smtp())
                smtp_conn.quit()
                PrintStyle().success("SMTP connection test successful")
            except Exception as e:
                raise Exception(f"SMTP connection test failed: {str(e)}")
                
        finally:
            test_connection.cleanup()
            loop.close()

    async def execute(self, **kwargs) -> Response:
        """
        Execute email operations based on method.

        Supported methods:
        - check_inbox: List unread emails
        - read_email: Read specific email by ID
        - send_email: Send new email
        - reply_email: Reply to existing email
        - list_folders: List IMAP folders
        - mark_read: Mark email as read
        - move_email: Move email to folder
        """
        try:
            # Check if email service is initialized
            if not self.is_initialized:
                error_msg = f"Email service not initialized: {self.initialization_error or 'Unknown error'}"
                PrintStyle().error(error_msg)
                return Response(message=error_msg, break_loop=False)
            
            self.connection = EmailConnection(self.config)

            if self.method == "check_inbox":
                return await self.check_inbox(**kwargs)
            elif self.method == "read_email":
                return await self.read_email(**kwargs)
            elif self.method == "send_email":
                return await self.send_email(**kwargs)
            elif self.method == "reply_email":
                return await self.reply_email(**kwargs)
            elif self.method == "list_folders":
                return await self.list_folders(**kwargs)
            elif self.method == "mark_read":
                return await self.mark_read(**kwargs)
            elif self.method == "move_email":
                return await self.move_email(**kwargs)
            else:
                return Response(
                    message=f"Unknown email method: {self.method}. Supported methods: check_inbox, read_email, send_email, reply_email, list_folders, mark_read, move_email",
                    break_loop=False,
                )

        except Exception as e:
            error_msg = f"Email operation failed: {str(e)}"
            PrintStyle().error(error_msg)
            return Response(message=error_msg, break_loop=False)
        finally:
            if self.connection:
                self.connection.cleanup()

    async def check_inbox(
        self, folder: str = "INBOX", status: str = "UNSEEN"
    ) -> Response:
        """Check for emails in specified folder with given status."""
        try:
            self.log.update(progress="Connecting to IMAP server...")
            imap_conn = await self.connection.connect_imap()

            self.log.update(progress=f"Selecting folder: {folder}")
            imap_conn.select(folder)

            self.log.update(progress=f"Searching for {status} emails...")
            search_status, data = imap_conn.search(None, status)

            if search_status != "OK":
                return Response(
                    message=f"Failed to search emails: {search_status}",
                    break_loop=False,
                )

            email_ids = [eid.decode() for eid in data[0].split()] if data[0] else []

            result = {
                "folder": folder,
                "status": status,
                "count": len(email_ids),
                "email_ids": email_ids,
            }

            self.log.update(progress=f"Found {len(email_ids)} emails")
            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"Check inbox failed: {str(e)}")

    async def read_email(self, email_id: str, folder: str = "INBOX") -> Response:
        """Read specific email by ID."""
        try:
            self.log.update(progress="Connecting to IMAP server...")
            imap_conn = await self.connection.connect_imap()

            self.log.update(progress=f"Selecting folder: {folder}")
            imap_conn.select(folder)

            self.log.update(progress=f"Fetching email ID: {email_id}")
            status, msg_data = imap_conn.fetch(email_id, "(RFC822)")

            if status != "OK":
                return Response(
                    message=f"Failed to fetch email: {status}", break_loop=False
                )

            msg = email.message_from_bytes(msg_data[0][1])

            # Extract email details
            result = {
                "id": email_id,
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "date": msg.get("Date", ""),
                "body": self._extract_body(msg),
                "attachments": self._extract_attachments(msg),
            }

            self.log.update(progress="Email successfully read")
            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"Read email failed: {str(e)}")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        attachments: List[str] = None,
        format: str = "plain",
    ) -> Response:
        """Send new email with support for plain text and HTML formats."""
        try:
            self.log.update(progress="Preparing email message...")

            # Validate format parameter
            format = format.lower().strip()
            if format not in ["plain", "html"]:
                format = "plain"  # Default to plain text for invalid formats

            # Create message
            msg = MIMEMultipart()
            msg["From"] = formataddr((self.config.from_name, self.config.username))
            msg["To"] = to
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = cc

            # Add body with specified format
            msg.attach(MIMEText(body, format))

            # Add attachments if provided
            if attachments:
                await self._add_attachments(msg, attachments)

            # Connect and send
            self.log.update(progress="Connecting to SMTP server...")
            smtp_conn = await self.connection.connect_smtp()

            # Prepare recipient list
            recipients = [to]
            if cc:
                recipients.extend([addr.strip() for addr in cc.split(",")])
            if bcc:
                recipients.extend([addr.strip() for addr in bcc.split(",")])

            self.log.update(
                progress=f"Sending email to {len(recipients)} recipient(s)..."
            )
            smtp_conn.sendmail(self.config.username, recipients, msg.as_string())

            result = {
                "status": "sent",
                "to": to,
                "subject": subject,
                "format": format,
                "recipients": len(recipients),
                "attachments": len(attachments) if attachments else 0,
            }

            self.log.update(progress="Email sent successfully")
            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"Send email failed: {str(e)}")

    async def reply_email(
        self, email_id: str, body: str, folder: str = "INBOX", reply_all: bool = False
    ) -> Response:
        """Reply to existing email."""
        try:
            # First read the original email
            self.log.update(progress="Reading original email...")
            read_response = await self.read_email(email_id, folder)
            original_email = json.loads(read_response.message)

            # Extract reply information
            original_from = original_email.get("from", "")
            original_subject = original_email.get("subject", "")

            # Parse sender address
            sender_name, sender_email = parseaddr(original_from)
            if not sender_email:
                return Response(
                    message="Cannot extract sender email address for reply",
                    break_loop=False,
                )

            # Prepare reply
            reply_subject = (
                f"Re: {original_subject}"
                if not original_subject.startswith("Re:")
                else original_subject
            )

            # Determine recipients
            to_address = sender_email
            cc_addresses = ""

            if reply_all:
                # Parse To and CC from original email
                original_email.get("to", "")
                # Add logic for reply-all if needed

            self.log.update(progress="Sending reply...")
            return await self.send_email(
                to=to_address, subject=reply_subject, body=body, cc=cc_addresses
            )

        except Exception as e:
            raise Exception(f"Reply email failed: {str(e)}")

    async def list_folders(self) -> Response:
        """List available IMAP folders."""
        try:
            self.log.update(progress="Connecting to IMAP server...")
            imap_conn = await self.connection.connect_imap()

            self.log.update(progress="Listing folders...")
            status, folders = imap_conn.list()

            if status != "OK":
                return Response(
                    message=f"Failed to list folders: {status}", break_loop=False
                )

            folder_list = []
            for folder in folders:
                folder_info = folder.decode().split(' "/" ')
                if len(folder_info) >= 2:
                    folder_list.append(folder_info[1].strip('"'))

            result = {"folders": folder_list, "count": len(folder_list)}

            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"List folders failed: {str(e)}")

    async def mark_read(self, email_id: str, folder: str = "INBOX") -> Response:
        """Mark email as read."""
        try:
            self.log.update(progress="Connecting to IMAP server...")
            imap_conn = await self.connection.connect_imap()

            self.log.update(progress=f"Selecting folder: {folder}")
            imap_conn.select(folder)

            self.log.update(progress=f"Marking email {email_id} as read...")
            imap_conn.store(email_id, "+FLAGS", "\\Seen")

            result = {"email_id": email_id, "folder": folder, "status": "marked_read"}

            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"Mark read failed: {str(e)}")

    async def move_email(
        self, email_id: str, from_folder: str = "INBOX", to_folder: str = "Archive"
    ) -> Response:
        """Move email to different folder."""
        try:
            self.log.update(progress="Connecting to IMAP server...")
            imap_conn = await self.connection.connect_imap()

            self.log.update(progress=f"Selecting folder: {from_folder}")
            imap_conn.select(from_folder)

            self.log.update(progress=f"Moving email {email_id} to {to_folder}...")
            imap_conn.move(email_id, to_folder)
            imap_conn.expunge()

            result = {
                "email_id": email_id,
                "from_folder": from_folder,
                "to_folder": to_folder,
                "status": "moved",
            }

            return Response(message=json.dumps(result, indent=2), break_loop=False)

        except Exception as e:
            raise Exception(f"Move email failed: {str(e)}")

    def _extract_body(self, msg: email.message.Message) -> str:
        """Extract email body text."""
        body = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode(errors="ignore")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")
        except Exception:
            body = "Error extracting email body"

        return body.strip()

    def _extract_attachments(self, msg: email.message.Message) -> List[Dict[str, Any]]:
        """Extract attachment information."""
        attachments = []
        try:
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename:
                        attachments.append(
                            {
                                "filename": filename,
                                "content_type": part.get_content_type(),
                                "size": len(part.get_payload(decode=True) or b""),
                            }
                        )
        except Exception:
            pass

        return attachments

    async def _add_attachments(self, msg: MIMEMultipart, attachment_paths: List[str]):
        """Add file attachments to email message."""
        for file_path in attachment_paths:
            try:
                if not files.exists(file_path):
                    PrintStyle().warning(f"Attachment file not found: {file_path}")
                    continue

                # Read file
                with open(file_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                # Encode in base64
                encoders.encode_base64(part)

                # Add header
                filename = os.path.basename(file_path)
                part.add_header(
                    "Content-Disposition", f"attachment; filename= {filename}"
                )

                msg.attach(part)

            except Exception as e:
                PrintStyle().warning(f"Failed to attach file {file_path}: {str(e)}")

    def get_log_object(self):
        """Create custom log object for email operations."""
        method_icons = {
            "check_inbox": "inbox",
            "read_email": "mail_outline",
            "send_email": "send",
            "reply_email": "reply",
            "list_folders": "folder",
            "mark_read": "mark_email_read",
            "move_email": "drive_file_move",
        }

        icon = method_icons.get(self.method, "email")
        method_name = self.method or "email_operation"

        return self.agent.context.log.log(
            type="email",
            heading=f"icon://{icon} {self.agent.agent_name}: Email {method_name.replace('_', ' ').title()}",
            content="",
            kvps=self.args,
        )

    async def before_execution(self, **kwargs):
        """Custom pre-execution setup."""
        await super().before_execution(**kwargs)
        self.log.update(progress="Initializing email operation...")

    async def after_execution(self, response: Response, **kwargs):
        """Custom post-execution cleanup."""
        if self.connection:
            self.connection.cleanup()
        await super().after_execution(response, **kwargs)
