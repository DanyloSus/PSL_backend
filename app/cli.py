"""Project CLI (`uv run psl <command>`)."""

from __future__ import annotations

import asyncio

import typer

from app.core.db import dispose_engine, get_sessionmaker
from app.core.security import hash_password
from app.models.user import UserRole
from app.repositories.user_repo import UserRepository
from app.services.user_service import UserService

cli = typer.Typer(help="PSL backend CLI", add_completion=False, no_args_is_help=True)


@cli.callback()
def _root() -> None:
    """PSL backend CLI."""


@cli.command("create-admin")
def create_admin(
    email: str = typer.Option(..., help="Admin email"),
    username: str = typer.Option(..., help="Admin username"),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
) -> None:
    """Create or promote an ADMIN user."""

    async def _run() -> None:
        sm = get_sessionmaker()
        async with sm() as session:
            users = UserRepository(session)
            existing = await users.get_by_email(email)
            if existing is not None:
                existing.role = UserRole.ADMIN
                existing.password_hash = hash_password(password)
                existing.username = username
                await session.commit()
                typer.echo(f"Promoted existing user {existing.email} to ADMIN.")
                return
            user = await users.create(
                email=email,
                username=username,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
            )
            await UserService(session).initialize_user_stats(user.id)
            await session.commit()
            typer.echo(f"Created ADMIN user {user.email} ({user.id}).")
        await dispose_engine()

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
