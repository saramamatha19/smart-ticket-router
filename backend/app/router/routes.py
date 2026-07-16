# Used for structured, filterable logs instead of print()
import logging

# Import APIRouter
from fastapi import APIRouter, Depends, HTTPException, Query, Response

# SQLAlchemy Session
from sqlalchemy.orm import Session

# Database dependency
from app.database.connection import get_db

# Route auth guards
from app.auth.dependencies import get_current_admin, get_current_customer

# Schemas
from app.schemas.ticket_schema import TicketRequest, TicketResponse

# AI Service
from app.services.router_service import route_ticket

# CRUD functions
from app.crud.ticket_crud import (
    save_tickets,
    get_all_tickets,
    get_ticket_count,
    get_ticket_stats,
    get_tickets_by_customer,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Route a ticket using AI. A message with multiple independent requests
# (e.g. a billing issue and an unrelated joke request) comes back as
# multiple entries -- one per request -- each routed/classified on its
# own, which is why this returns a list even for the common single-intent
# case.
@router.post("/route-ticket", response_model=list[TicketResponse])
def classify_ticket(
    ticket: TicketRequest,
    db: Session = Depends(get_db),
    customer_id: int = Depends(get_current_customer),
):

    try:
        # Get AI response(s) -- one per distinct request in the message
        results = route_ticket(ticket.message)

    except Exception:
        # Log the full detail server-side; never expose raw exception
        # internals (stack traces, API keys in error messages, etc.)
        # to the client.
        logger.error("AI routing failed for an incoming ticket", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="AI routing is temporarily unavailable. Please try again.",
        )

    # Save to PostgreSQL, tied to the submitting customer
    save_tickets(db, ticket.message, results, customer_id=customer_id)

    # Return AI response(s)
    return results


# Get saved tickets, newest first.
# limit/offset are optional — omitting them returns everything, exactly
# like before. They exist so a growing ticket volume has a paging path
# without a breaking change to the existing frontend call. The response
# *body* stays a bare array (unchanged contract); the total row count
# is exposed via the X-Total-Count header instead, so a caller using
# limit can tell how many pages exist without a second request, and any
# caller ignoring headers (like today's frontend) sees no difference.
@router.get("/tickets")
def all_tickets(
    response: Response,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _admin: str = Depends(get_current_admin),
):

    response.headers["X-Total-Count"] = str(get_ticket_count(db))
    return get_all_tickets(db, limit=limit, offset=offset)


# Get dashboard analytics (totals by priority/category/sentiment)
@router.get("/tickets/stats")
def ticket_stats(db: Session = Depends(get_db), _admin: str = Depends(get_current_admin)):

    return get_ticket_stats(db)


# A customer's own ticket history, newest first -- unlike /tickets
# (admin-only, sees everything), this is scoped to the logged-in
# customer's own submissions.
@router.get("/tickets/mine")
def my_tickets(
    db: Session = Depends(get_db),
    customer_id: int = Depends(get_current_customer),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):

    return get_tickets_by_customer(db, customer_id, limit=limit, offset=offset)