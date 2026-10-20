import tomllib
from typing import Annotated
from pathlib import Path
from pydantic import BaseModel, Field,  StringConstraints



class Settings(BaseModel):
    model: Annotated[str,StringConstraints(
        strip_whitespace=True,
        min_length=1,
    )] = Field(
        default="qwen3:1.7b",
        description="Your installed Ollama model’s name"
    )
    base_url:Annotated[str,StringConstraints(
        strip_whitespace=True,
        min_length=1,
    )]  = Field(
        default="http://localhost:11434",
        description="Your Ollama Base URL"
    )
    temperature:float = Field(
        default=0.23,
        description="Your Ollama Temperature"#simply higher temp means higher creative freedom
        ,ge=0
        ,le=1
    )
    request_timeout:float = Field(
        default=120,
        description="Your Ollama Request Timeout in seconds",
        gt=0
    )
    history_limit:int = Field(
        default=10,
        description="Maximum number of recent Git commit titles used as style context.",
        gt=0
    )
    max_diff_chars:int = Field(
        default=12000,
        description="Maximum number of diff characters allowed before chunking or summarization.",
        gt=0
    )

def load_settings(configration_file_path:None|str|Path = None) -> Settings:

    settings=Settings()
    if configration_file_path is None:
        return settings
    with open(configration_file_path,"rb") as f:
        resulting_dict = tomllib.load(f)
        # settings.model=resulting_dict["model"]
        # settings.base_url=resulting_dict["base_url"]
        # settings.temperature=resulting_dict["temperature"]
    return Settings(**resulting_dict)
