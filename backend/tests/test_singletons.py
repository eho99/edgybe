import pytest
from app.db import engine as db_engine, get_db
from app.auth import supabase as auth_supabase
from sqlalchemy.engine import Engine
from supabase import Client

def test_db_engine_is_singleton():
    """Ensures the engine object is a singleton."""
    from app.db import engine as db_engine2
    assert db_engine is db_engine2
    assert isinstance(db_engine, Engine)

def test_supabase_client_is_singleton():
    """Ensures the supabase client object is a singleton."""
    from app.auth import supabase as auth_supabase2
    assert auth_supabase is auth_supabase2
    assert isinstance(auth_supabase, Client)

def test_get_db_yields_session():
    """Tests that get_db yields a session and closes it."""
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    # Check that the generator closes the session
    with pytest.raises(StopIteration):
        next(db_gen)
