# Used to interact with the database

# Used to generate a shared group_id for tickets split from one message
import uuid

#func gives access to sql functions.
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ticket import Ticket


# Save a single ticket into PostgreSQL
def save_ticket(db: Session, message, ai_result, group_id=None, customer_id=None):

    ticket = Ticket(

        message=message,

        group_id=group_id,

        customer_id=customer_id,

        category=ai_result.category,

        priority=ai_result.priority,

        assigned_team=ai_result.assigned_team,

        reason=ai_result.reason,

        confidence=ai_result.confidence,

        sentiment=ai_result.sentiment,

        summary=ai_result.summary,

        keywords=ai_result.keywords,

        estimated_resolution_time=ai_result.estimated_resolution_time,

        suggested_reply=ai_result.suggested_reply,

        escalation_needed=ai_result.escalation_needed,

        needs_human_review=ai_result.needs_human_review
    )

    # Add ticket to database
    db.add(ticket)

    # Save changes
    db.commit()

    # Refresh to get generated values like id
    db.refresh(ticket)

    return ticket


def save_tickets(db: Session, message, ai_results, customer_id=None):

    group_id = str(uuid.uuid4()) if len(ai_results) > 1 else None

    return [
        save_ticket(db, message, ai_result, group_id=group_id, customer_id=customer_id)
        for ai_result in ai_results
    ]

def get_all_tickets(db: Session, limit: int | None = None, offset: int = 0):

    query = db.query(Ticket).order_by(Ticket.id.desc()).offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query.all()

def get_tickets_by_customer(db: Session, customer_id: int, limit: int | None = None, offset: int = 0):

    query = (
        db.query(Ticket)
        .filter(Ticket.customer_id == customer_id)
        .order_by(Ticket.id.desc())
        .offset(offset)
    )

    if limit is not None:
        query = query.limit(limit)

    return query.all()

def get_ticket_count(db: Session):

    return db.query(func.count(Ticket.id)).scalar()


# Get dashboard aggregate counts (used by the analytics cards + chart)
def get_ticket_stats(db: Session):

    total = db.query(func.count(Ticket.id)).scalar()

    def counts_by(column):
        rows = (
            db.query(column, func.count(Ticket.id))
            .group_by(column)
            .all()
        )
        return {value: count for value, count in rows}

    needs_review_count = (
        db.query(func.count(Ticket.id)).filter(Ticket.needs_human_review.is_(True)).scalar()
    )

    return {
        "total": total,
        "by_priority": counts_by(Ticket.priority),
        "by_category": counts_by(Ticket.category),
        "by_sentiment": counts_by(Ticket.sentiment),
        "needs_human_review_count": needs_review_count,
    }