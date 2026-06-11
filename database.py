from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase
from contextlib import contextmanager
from dotenv import dotenv_values

# Base class for models
class Base(DeclarativeBase):
    pass

# Create engine
# engine = create_engine("sqlite:///asf-orders-management.db", echo=False)


env = dotenv_values('.env')

engine = create_engine(
    f"postgresql+psycopg2://{env.get('username')}:{env.get('password')}@{env.get('host')}:{env.get('port')}/{env.get('db')}",
    connect_args={
        "sslmode": "verify-ca",
        "sslrootcert": "./ca.pem"
    }
)


# Context manager for session
@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    """Create all tables."""
    import models  # IMPORTANT: import here so Order is registered
    Base.metadata.create_all(bind=engine)
