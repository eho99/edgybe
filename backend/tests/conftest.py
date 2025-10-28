import pytest
from dotenv import load_dotenv
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='session', autouse=True)
def load_test_env():
    load_dotenv(dotenv_path='backend/.env.test')
