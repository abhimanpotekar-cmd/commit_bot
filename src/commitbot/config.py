import tomllib
from typing import Annotated,List
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
    exclude_patterns:List[str] = Field(
        default_factory=lambda: [".env", ".env.*", "*.pem", "*.key", "uv.lock", "package-lock.json"],#default_factory requires a callable returning a list rather than the list itself
        description="Repository-relative file patterns excluded from model context",
    )

def load_settings(configration_file_path: None | str | Path = None) -> Settings:

    if configration_file_path is not None:
        path = Path(configration_file_path)
        with open(path, "rb") as f:
            resulting_dict = tomllib.load(f)
        return Settings(**resulting_dict)


    default_config = Path("commitbot.toml")
    if default_config.is_file():
        with open(default_config, "rb") as f:
            resulting_dict = tomllib.load(f)
        return Settings(**resulting_dict)


    return Settings()


if __name__ == "__main__":
    settings = load_settings()
    print("Loaded model:", settings.model)
    print("History limit:", settings.history_limit)
    print("Exclude patterns:", settings.exclude_patterns)