from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ConfluencePageModel(BaseModel):
    id: str = Field(
        title="Unique identifier for the resource",
        default_factory=lambda: str(uuid4())
    )

    page_id: str = Field(
        ...,
        description="The unique identifier for the Confluence page.",
    )
    title: str = Field(
        ...,
        description="The title of the Confluence page.",
    )
    body: str = Field(
        ...,
        description="The content of the Confluence page.",
    )
    space: str = Field(
        ...,
        description="The name of the Confluence space.",
    )
    space_id: int = Field(
        ...,
        description="The unique identifier for the Confluence space.",
    )
    space_key: str = Field(
        ...,
        description="The key of the Confluence space.",
    )
    type: str = Field(
        ...,
        description="The type of the Confluence page.",
    )
    last_update: datetime = Field(
        ...,
        description="The date and time when the page was last updated.",
    )
    last_updater: str = Field(
        ...,
        description="The name of the user who last updated the page.",
    )
    indexed: bool = Field(
        False,
        description="Indicates whether the page is indexed.",
    )
    version: int = Field(
        ...,
        description="The version of the Confluence page.",
    )
    last_indexed_at: Optional[datetime] = Field(
        ...,
        description="The date and time when the page was last indexed.",
    )
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="The date and time when the page was created.",
    )
