from dotenv import load_dotenv
load_dotenv()
import os
def get_github_token()->str|None:
    github_token=os.getenv("GITHUB_TOKEN")
    if github_token is not None and github_token.strip()!= "":
        return github_token.strip()
    else:
        return None
