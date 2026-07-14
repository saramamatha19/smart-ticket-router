# Used to interact with the database

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ticket import Ticket


# Save a ticket into PostgreSQL
def save_ticket(db: Session, message, ai_result):

    ticket = Ticket(

        message=message,

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


# Get tickets, newest first. limit/offset are optional so the existing
# "give me everything" call (no params) behaves exactly as before —
# this only adds the *capability* to page through results.
def get_all_tickets(db: Session, limit: int | None = None, offset: int = 0):

    query = db.query(Ticket).order_by(Ticket.id.desc()).offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query.all()


# Total row count, used to expose X-Total-Count alongside a paginated
# /tickets response -- a single SQL COUNT, not len() on a fetched list.
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