from dotenv import load_dotenv
load_dotenv()  # Loads .env variables before app starts[^2][^5]

from .routes import run_app

run_app()
