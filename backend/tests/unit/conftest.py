import os

# Set required env vars before any app module is imported
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
