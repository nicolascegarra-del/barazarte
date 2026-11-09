"""CLI de administracion. Crea artistas (y administradores) ya verificados.

Uso: python -m app.cli create-artist --email maria@example.com --name "Maria" [--admin]
     python -m app.cli generate-vapid
"""

import argparse
import base64
import getpass
import sys

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
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


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def generate_vapid_keys() -> tuple[str, str]:
    """Par VAPID (P-256). Publica: punto sin comprimir en base64url (applicationServerKey del
    navegador). Privada: escalar de 32 bytes en base64url (formato que acepta pywebpush)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_bytes = private_key.public_key().public_bytes(
        Encoding.X962, PublicFormat.UncompressedPoint
    )
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")
    return _b64url(public_bytes), _b64url(private_bytes)


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-artist", help="Crea una cuenta de artista")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--admin", action="store_true", help="Crea un administrador")
    sub.add_parser("generate-vapid", help="Genera un par de claves VAPID para Web Push")
    args = parser.parse_args()

    if args.command == "generate-vapid":
        public_key, private_key = generate_vapid_keys()
        sys.stdout.write(f"VAPID_PUBLIC_KEY={public_key}\nVAPID_PRIVATE_KEY={private_key}\n")
        return

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
