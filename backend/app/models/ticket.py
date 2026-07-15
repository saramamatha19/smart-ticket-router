# Import required SQLAlchemy classes
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text

# Used to automatically store the current date and time
from datetime import datetime

# Import Base class
from app.database.connection import Base


# Ticket table
class Ticket(Base):

    # Table name in PostgreSQL
    __tablename__ = "tickets"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Customer's support message
    message = Column(String, nullable=False)

    # Ties multiple rows together when one submitted message contained
    # several independent requests split into separate tickets (see
    # router_service.route_ticket / TicketBatchResponse). Null for
    # tickets saved before this existed. Not unique -- shared by every
    # sub-ticket that came from the same submission.
    group_id = Column(String, nullable=True, index=True)

    # AI predicted category — indexed since /tickets/stats groups by it
    category = Column(String, nullable=False, index=True)

    # AI predicted priority — indexed since /tickets/stats groups by it
    priority = Column(String, nullable=False, index=True)

    # Team assigned by AI
    assigned_team = Column(String, nullable=False)

    # One-line explanation
    reason = Column(String, nullable=False)

    # Time when ticket was created — indexed for future date-range filtering/reporting
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # -------------------------------------------------
    # Extended AI analysis fields
    # Nullable so this doesn't break if the table already
    # existed before these columns were added.
    # -------------------------------------------------

    # How confident the AI is in this classification (0-100)
    confidence = Column(Integer, nullable=True)

    # Customer's emotional tone (Positive, Neutral, Angry)
    sentiment = Column(String, nullable=True)

    # One-sentence plain language summary of the issue
    summary = Column(String, nullable=True)

    # Relevant keywords extracted from the ticket
    keywords = Column(JSON, nullable=True)

    # Human-readable estimate, e.g. "1-4 Hours"
    estimated_resolution_time = Column(String, nullable=True)

    # AI-drafted reply to the customer
    suggested_reply = Column(Text, nullable=True)

    # Whether this ticket should be escalated
    escalation_needed = Column(Boolean, nullable=True)

    # True if confidence < router_service.CONFIDENCE_REVIEW_THRESHOLD.
    # Computed deterministically server-side, not trusted from the
    # model's own guess -- see _apply_human_review_flag().
    needs_human_review = Column(Boolean, nullable=True)

'''
This file tells SQLAlchemy:
"I have a table named tickets, and these are its columns."
'''