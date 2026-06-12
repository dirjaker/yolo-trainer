"""Team service — CRUD operations for teams and members."""

import uuid

from sqlalchemy.orm import Session

from app.models.team import Team, TeamMember
from app.schemas.team import TeamCreate, TeamUpdate


def create_team(db: Session, owner_id: uuid.UUID, data: TeamCreate) -> Team:
    """Create a new team and add the owner as a member."""
    team = Team(
        name=data.name,
        description=data.description,
        owner_id=owner_id,
    )
    db.add(team)
    db.flush()  # get team.id

    owner_member = TeamMember(
        team_id=team.id,
        user_id=owner_id,
        role="owner",
    )
    db.add(owner_member)
    db.commit()
    db.refresh(team)
    return team


def get_teams(db: Session, user_id: uuid.UUID) -> list[Team]:
    """Return all teams the user belongs to."""
    return (
        db.query(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .filter(TeamMember.user_id == user_id)
        .all()
    )


def get_team(db: Session, team_id: uuid.UUID) -> Team | None:
    """Return a single team by id."""
    return db.query(Team).filter(Team.id == team_id).first()


def update_team(db: Session, team: Team, data: TeamUpdate) -> Team:
    """Update team fields."""
    if data.name is not None:
        team.name = data.name
    if data.description is not None:
        team.description = data.description
    db.commit()
    db.refresh(team)
    return team


def add_member(db: Session, team_id: uuid.UUID, user_id: uuid.UUID, role: str = "member") -> TeamMember:
    """Add a user to a team."""
    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if existing:
        raise ValueError("User is already a member of this team")

    member = TeamMember(team_id=team_id, user_id=user_id, role=role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_member(db: Session, team_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Remove a user from a team."""
    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if not member:
        raise ValueError("User is not a member of this team")
    if member.role == "owner":
        raise ValueError("Cannot remove the team owner")

    db.delete(member)
    db.commit()
