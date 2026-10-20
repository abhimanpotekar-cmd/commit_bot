from langchain_ollama import ChatOllama

from commitbot.config import  Settings


def create_chat_model(settings: Settings)->ChatOllama:
    """
       Construct and return a ChatOllama instance based on Settings.
       Only handles model setup; generation belongs in generator.py.
       """
    return ChatOllama(model=settings.model,
                      base_url=settings.base_url
                      ,temperature=settings.temperature,
                      client_kwargs={
                          "timeout": settings.request_timeout
                      }
                      )