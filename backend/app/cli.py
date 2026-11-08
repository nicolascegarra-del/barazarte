"""CLI de administracion. Crea artistas (y administradores) ya verificados.

Uso: python -m app.cli create-artist --email maria@example.com --name "Maria" [--admin]
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


def create_artist(email: str, display_name: str, password: str, *, is_admin: bool = False) -> None:
    with Session(get_engine()) as session:
        if session.exec(select(Artist).where(Artist.email == email.lower())).first():
            raise SystemExit(f"Ya existe un artista con el email {email}")
        session.add(
            Artist(
                email=email.lower(),
                display_name=display_name,
                password_hash=hash_password(password),
                email_verified=True,
                is_admin=is_admin,
                # Un admin no tiene limite de obras; el resto usa DEFAULT_MAX_ARTWORKS
                **({"max_artworks": None} if is_admin else {}),
            )
        )
        session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-artist", help="Crea una cuenta de artista")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--admin", action="store_true", help="Crea un administrador")
    args = parser.parse_args()

    password = getpass.getpass("Contrasena: ")
    if getpass.getpass("Repite la contrasena: ") != password:
        sys.exit("Las contrasenas no coinciden")
    if len(password) < MIN_PASSWORD_LENGTH or len(password.encode()) > MAX_PASSWORD_BYTES:
        sys.exit(
            f"La contrasena debe tener entre {MIN_PASSWORD_LENGTH} y {MAX_PASSWORD_BYTES} bytes"
        )
    create_artist(args.email, args.name, password, is_admin=args.admin)
    sys.stdout.write("Administrador creado\n" if args.admin else "Artista creado\n")


if __name__ == "__main__":
    main()
