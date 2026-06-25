"""Team API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamListResponse,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
)
from app.services import team_service

router = APIRouter()


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new team — current user becomes owner."""
    return team_service.create_team(db, owner_id=current_user.id, data=data)


@router.get("/teams", response_model=TeamListResponse)
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all teams the current user belongs to."""
    teams = team_service.get_teams(db, user_id=current_user.id)
    return TeamListResponse(items=teams, total=len(teams))


@router.get("/teams/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single team by ID."""
    team = team_service.get_team(db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.patch("/teams/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: uuid.UUID,
    data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a team (owner only)."""
    team = team_service.get_team(db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can update the team")
    return team_service.update_team(db, team=team, data=data)


@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    team_id: uuid.UUID,
    data: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a member to a team."""
    team = team_service.get_team(db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can add members")
    try:
        return team_service.add_member(db, team_id=team_id, user_id=data.user_id, role=data.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/teams/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from a team."""
    team = team_service.get_team(db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can remove members")
    try:
        team_service.remove_member(db, team_id=team_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
