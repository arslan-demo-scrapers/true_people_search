from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")
