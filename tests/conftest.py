import os

# Set environment variables BEFORE importing settings or any backend components
os.environ["DATABASE_URL"] = "sqlite:///./test_ai_code_reviewer.db"
os.environ["LLM_PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "mock_groq_api_key_value_here"
os.environ["GEMINI_API_KEY"] = "mock_gemini_api_key_value_here"
os.environ["DEBUG"] = "True"

import pytest

pytest_plugins = [
    "tests.fixtures.db_fixtures",
    "tests.fixtures.mock_fixtures",
    "tests.fixtures.payload_fixtures",
]

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    # After the entire test session completes, clean up the test SQLite DB and WAL files
    db_files = [
        "test_ai_code_reviewer.db",
        "test_ai_code_reviewer.db-shm",
        "test_ai_code_reviewer.db-wal"
    ]
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass
