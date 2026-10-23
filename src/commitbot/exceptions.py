class CommitBotError(Exception):
    pass
class GitNotInstalledError(CommitBotError):
    pass
class NotGitRepositoryError(CommitBotError):
    pass
class GitCommandError(CommitBotError):
    pass
class ModelConnectionError(CommitBotError):
    pass
class ModelTimeoutError(CommitBotError):
    pass
class ModelResponseError(CommitBotError):
    pass
