from dotenv import load_dotenv
load_dotenv(override=True)
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
DBNAME = os.getenv("DBNAME")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
PORT = os.getenv("PORT")
HOST = os.getenv("HOST")