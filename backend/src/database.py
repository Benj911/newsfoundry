import os
import bcrypt
from sqlmodel import SQLModel, Session, create_engine, select
from models import User

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
    print("Database initialized successfully")

    # Creating a default user
    default_email = "test@test.com"
    default_password = "test"

    with Session(engine) as session:
        statement = select(User).where(User.email == default_email)
        user = session.exec(statement).first()

        if not user:
            # Encodage du hash en chaîne pour stockage standard
            hashed = bcrypt.hashpw(
                default_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            session.add(User(email=default_email, hashed_password=hashed))
            session.commit()