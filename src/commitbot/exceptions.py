class CommitBotError(Exception):
    pass
class GitNotInstalledError(CommitBotError):
    pass
class NotGitRepositoryError(CommitBotError):
    pass
class GitCommandError(CommitBotError):
    pass