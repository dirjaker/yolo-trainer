"""Team schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TeamCreate(BaseModel):
    """Schema for creating a team."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class TeamMemberCreate(BaseModel):
    """Schema for adding a team member."""
    user_id: UUID
    role: str = Field(default="member", pattern=r"^(owner|admin|member)$")


class TeamMemberResponse(BaseModel):
    """Schema for team member response."""
    team_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    """Schema for team response."""
    id: UUID
    name: str
    description: Optional[str] = None
    owner_id: UUID
    created_at: datetime
    members: list[TeamMemberResponse] = []

    class Config:
        from_attributes = True


class TeamListResponse(BaseModel):
    """Schema for team list response."""
    items: list[TeamResponse]
    total: int
