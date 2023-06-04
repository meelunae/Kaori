from dotenv import load_dotenv
import os

class Config:
    def __init__(self):
        load_dotenv()

        self.kaori_token = os.getenv("KAORI_AUTH_TOKEN")
        self.kaori_id = int(os.getenv("KAORI_ID"))
        self.owner_id = int(os.getenv("OWNER_ID"))
        self.configured_prefix = os.getenv("COMMAND_PREFIX") or "!"

        if self.kaori_token is None:
            self.cfg_error("KAORI_AUTH_TOKEN")

        if self.kaori_id is None:
            self.cfg_error("KAORI_ID")

        if self.owner_id is None:
            self.cfg_error("OWNER_ID")
        
        if self.configured_prefix is None:
            self.cfg_error("COMMAND_PREFIX")

    def cfg_error(key):
        print(f"ERROR: .env file is not configured properly, missing {key}")

cfg = Config()