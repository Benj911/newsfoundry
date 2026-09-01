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

    default_email = "test@test.com"
    default_password = "test"

    # Génération d'un hash bcrypt propre
    salt = bcrypt.gensalt()
    new_hashed_password = bcrypt.hashpw(default_password.encode("utf-8"), salt).decode("utf-8")

    with Session(engine) as session:
        statement = select(User).where(User.email == default_email)
        user = session.exec(statement).first()

        if not user:
            session.add(User(email=default_email, hashed_password=new_hashed_password))
            session.commit()
        else:
            # Force la mise à jour si le hash existant est corrompu/invalide
            user.hashed_password = new_hashed_password
            session.add(user)
            session.commit()