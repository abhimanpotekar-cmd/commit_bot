# Annotated is a typing helper that lets you attach metadata (like constraints) to a type.
from pydantic import BaseModel, Field, StringConstraints
from typing import List

from typing_extensions import Annotated


class CommitSuggestion(BaseModel):
    title: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=72
        )
    ] = Field(
        description="The title of the commit"
    )
    body:str|None = Field(
        default=None,
        description="The body of the commit",
    )

class CommitSuggestions(BaseModel):
    suggestions: List[CommitSuggestion]=Field(
        description="The list of suggestions",
        min_length=3,
        max_length=3,
    )
