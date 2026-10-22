import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
# Vacías (no borradas) para que load_dotenv no las rellene desde .env
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""