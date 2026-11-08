"""CLI de administracion. No hay registro publico: los artistas se crean desde aqui.

Uso: python -m app.cli create-artist --email maria@example.com --name "Maria"
"""

import argparse
import getpass
import sys

from sqlmodel import Session, select

from app.core.database import get_engine
from app.core.security import hash_password
from app.models import Artist

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_BYTES = 72  # limite de bcrypt


def create_artist(email: str, display_name: str, password: str) -> None:
    with Session(get_engine()) as session:
        if session.exec(select(Artist).where(Artist.email == email.lower())).first():
            raise SystemExit(f"Ya existe un artista con el email {email}")
        session.add(
            Artist(
                email=email.lower(),
                display_name=display_name,
                password_hash=hash_password(password),
            )
        )
        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-artist", help="Crea una cuenta de artista")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Contrasena: ")
    if getpass.getpass("Repite la contrasena: ") != password:
        sys.exit("Las contrasenas no coinciden")
    if len(password) < MIN_PASSWORD_LENGTH or len(password.encode()) > MAX_PASSWORD_BYTES:
        sys.exit(
            f"La contrasena debe tener entre {MIN_PASSWORD_LENGTH} y {MAX_PASSWORD_BYTES} bytes"
        )
    create_artist(args.email, args.name, password)
    sys.stdout.write("Artista creado\n")


if __name__ == "__main__":
    main()
