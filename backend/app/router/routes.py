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

@router.post("/route-ticket", response_model=list[TicketResponse])
def classify_ticket(
    ticket: TicketRequest,
    db: Session = Depends(get_db),
    customer_id: int = Depends(get_current_customer),
):

    try:
        results = route_ticket(ticket.message)

    except Exception:
        logger.error("AI routing failed for an incoming ticket", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="AI routing is temporarily unavailable. Please try again.",
        )

    # Save to PostgreSQL, tied to the submitting customer
    save_tickets(db, ticket.message, results, customer_id=customer_id)

    # Return AI response(s)
    return results

@router.get("/tickets")
def all_tickets(
    response: Response,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    #after authentication is added, this will be used to ensure only admins can call this endpoint
    _admin: str = Depends(get_current_admin),
):

    response.headers["X-Total-Count"] = str(get_ticket_count(db))
    return get_all_tickets(db, limit=limit, offset=offset)


# Get dashboard analytics (totals by priority/category/sentiment)
@router.get("/tickets/stats")
def ticket_stats(db: Session = Depends(get_db), _admin: str = Depends(get_current_admin)):

    return get_ticket_stats(db)


@router.get("/tickets/mine")
def my_tickets(
    db: Session = Depends(get_db),
    customer_id: int = Depends(get_current_customer),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):

    return get_tickets_by_customer(db, customer_id, limit=limit, offset=offset)