from dotenv import load_dotenv
import os

class Config:
    def __init__(self):
        load_dotenv()

        self.kaori_token = os.getenv("KAORI_AUTH_TOKEN")
        self.kaori_id = int(os.getenv("KAORI_ID"))
        self.owner_id = int(os.getenv("OWNER_ID"))

        if self.kaori_token is None:
            self.cfg_error("kaori_token")

        if self.kaori_id is None:
            self.cfg_error("kaori_id")

        if self.owner_id is None:
            self.cfg_error("owner_id")
        
    def cfg_error(key):
        print(f"ERROR: .env file is not configured properly, missing {key}")

cfg = Config()