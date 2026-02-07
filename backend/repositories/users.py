
from uuid import UUID

from pydantic import NameEmail

import sqlalchemy as sa
from sqlalchemy import insert, update, select
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


from model import User, ActiveTime, UserNotFoundError, safe_print_user

from usecases.users import UserRepo as UserRepoInterface


import logging
logger = logging.getLogger(__name__)

users_table = sa.Table(
    'users',
    sa.MetaData(),
    sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
    sa.Column('name', sa.String(50), unique=True, nullable=False),
    sa.Column('hashed_password', sa.String(255), nullable=False),
    sa.Column('active_from', sa.Integer()),
    sa.Column('active_to', sa.Integer()),
    sa.Column('email', sa.String(50), unique=True),
    sa.Column('telegram', sa.String(50), unique=True),
    sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(), server_onupdate=sa.func.now())
)

def user_from_row(tuple_like: tuple) -> User:
    return User(
        id=tuple_like[0],
        name=tuple_like[1],
        hashed_pasword=tuple_like[2],
        active_time=ActiveTime(from_hour=tuple_like[3], to_hour=tuple_like[4]),
        email=tuple_like[4],
        telegram=tuple_like[5],
        active=tuple_like[6]
    )

class UsersRepo(UserRepoInterface):
    async def add_nonactive(self, conn: AsyncConnection, user: User) -> User:
        stmt = insert(users_table).values(
            name=user.name,
            hashed_password=user.hashed_pasword,
            active_from=user.active_time.from_hour,
            active_to=user.active_time.to_hour,
            email=user.email,
            telegram=user.telegram,
            active=False
        )
        # only a temporary mesure, logging of hashed password is not safe
        logger.debug("formed add_nonactive request: %s", stmt)

        try:
            result = await conn.execute(stmt)
        except Exception as e:
            logger.info("failed to add user %s error %s", user, e)
            raise e
        new_user = user.model_copy({"id": result.inserted_primary_key})
        logger.info("added non-active user %s", new_user)
        return new_user

    async def activate(self, conn: AsyncConnection, id: UUID):
        stmt = update(users_table).where(users_table.c.id == id).values(active=True)
        logger.debug("formed activate request: %s", stmt)

        # it would also be good to check for error type and reraise with my own error types
        try:
            await conn.execute(stmt)
        except Exception as e:
            logger.info("failed to activate user with id %s error %s", id, e)
            raise e

        logger.info("successfully activated user with id %s", id)

    async def is_mail_used(self, conn: AsyncConnection, email: NameEmail) -> bool:
        stmt = select(sa.func.count("*")).select_from(users_table).where(users_table.c.email == email)
        logger.debug("formed is_mail_used request: %s", stmt)

        result = await conn.execute(stmt)
        used = result.first[0] != 0
        logger.debug("is_mail_used for %s: %s", email, used)
        return used

    async def is_telegram_used(self, conn: AsyncConnection, telegram: str) -> bool:
        stmt = select(sa.func.count("*")).select_from(users_table).where(users_table.c.telegram == telegram)
        logger.debug("formed is_telegram_used request: %s", stmt)

        result = await conn.execute(stmt)
        used = result.first[0] != 0
        logger.debug("is_telegram_used for %s: %s", telegram, used)
        return used

    async def get_user(self, conn: AsyncConnection, uuid: UUID) -> User:
        stmt = select(users_table).where(users_table.c.id == uuid)
        logger.debug("formed get_user request: %s", stmt)

        result = await conn.execute(stmt)
        
        if result.first:
            user = user_from_row(result.first)
        else:
            logger.debug("user with such id %s not found", uuid)
            raise UserNotFoundError(user_id=uuid)
        
        logger.debug("received user by id %s: %s", uuid, safe_print_user(user))
        return user

    async def get_by_username(self, conn: AsyncConnection, username: str) -> User:
        stmt = select(users_table).where(users_table.c.name == username)
        logger.debug("formed get_by_username request: %s", stmt)

        result = await conn.execute(stmt)
        
        if result.first:
            user = user_from_row(result.first)
        else:
            logger.debug("user with such username %s not found", username)
            raise UserNotFoundError(username=username)
        
        logger.debug("received user by username %s: %s", username, safe_print_user(user))
        return user

    async def update_user_info(self, conn: AsyncConnection, uuid: UUID, name: str | None = None, active_time: ActiveTime | None = None) -> User:
        stmt = update(users_table).where(users_table.c.id == uuid)
        if name and active_time:
            stmt = stmt.values(name=name, active_from=active_time.from_hour, to_hour=active_time.to_hour)
        elif name:
            stmt = stmt.values(name=name)
        elif active_time:
            stmt = stmt.values(active_from=active_time.from_hour, to_hour=active_time.to_hour)

        stmt = stmt.returning(users_table)
        logger.debug("formed update_user_info request: %s", stmt)

        try:
            result = await conn.execute(stmt)
        except Exception as e:
            logger.info("failed to update user with id %s with data: name = %s, active_time = %s; error %s", uuid, name, active_time, e)
            raise e

        if result.first:
            user = user_from_row(result.first)
        else:
            logger.info("no user with id %s found for update", uuid)
            raise UserNotFoundError(uuid=uuid)
        logger.info("successfully updated user with id %s with data: name = %s, active_time = %s; result = %s", uuid, name, active_time, user)
        return user

    async def update_user(self, conn: AsyncConnection, user: User) -> User:
        stmt = update(users_table).where(users_table.c.id == user.id).values(
            name=user.name,
            hashed_password=user.hashed_pasword,
            active_from=user.active_time.from_hour,
            active_to=user.active_time.to_hour,
            email=user.email,
            telegram=user.telegram,
            active=user.active
        )
        logger.debug("formed update_user request: %s", stmt)

        try:
            result = await conn.execute(stmt)
        except Exception as e:
            logger.info("failed to update user %s; error %s", user, e)
            raise e

        if result.first:
            user = user_from_row(result.first)
        else:
            logger.info("no user with id %s found for update", user.id)
            raise UserNotFoundError(uuid=user.id)
        logger.info("successfully updated user %s", user)
        return user