from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import insert, update, select, delete
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_Distance


from model import Good, GoodsList, LookFilter, GoodNotFoundError

from usecases.goods import GoodRepo as GoodRepoInterfaceGoods
from usecases.users import GoodRepo as GoodRepoInterfaceUsers


import logging
logger = logging.getLogger(__name__)

goods_table = sa.Table(
    'goods',
    sa.MetaData(),
    sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
    sa.Column('name', sa.String(150), unique=True, nullable=False),
    sa.Column('description', sa.String(1000)),
    sa.Column('price', sa.Float()),
    sa.Column('images', sa.ARRAY(sa.String(500))),
    sa.Column('location', Geography(geometry_type='POINT', srid=4326)),
    sa.Column('owner_id', PG_UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(), server_onupdate=sa.func.now())
)

def good_from_row(tuple_like: tuple) -> Good:
    raise NotImplementedError

class GoodRepo(GoodRepoInterfaceGoods, GoodRepoInterfaceUsers):
    async def add_good(self, conn: AsyncConnection, good: Good) -> Good:
        stmt = insert(goods_table).values(
            name=good.name,
            description=good.description,
            price=good.price,
            images=good.images,
            location=good.location,
            owner_id=good.owner_id
        )
        logger.debug("formed add_good request: %s", stmt)

        try:
            result = await conn.execute(stmt)
        except Exception as e:
            logger.debug("failed to add good %s error %s", good, e)
            raise e

        new_good = good.model_copy({"id": result.inserted_primary_key})
        logger.info("added new good %s", new_good)
        return new_good

    async def update_good(self, conn: AsyncConnection, good_id: UUID, good: Good) -> Good:
        stmt = update(goods_table).where(goods_table.c.id == good_id).values(
            name=good.name,
            description=good.description,
            price=good.price,
            images=good.images,
            location=good.location,
            owner_id=good.owner_id
        ).returning(goods_table)
        logger.debug("formed update_good request: %s", stmt)

        try:
            result = await conn.execute(stmt)
        except Exception as e:
            logger.debug("failed to update good %s with id %s error %s", good, good_id, e)
            raise e
        
        if result.first:
            good = good_from_row(result.first)
        else:
            logger.info("no good found for update with id %s", good_id)
            raise GoodNotFoundError(good_id)
        logger.info("successfully updated user with id %s with data %s", good_id, good)

        return good

    async def get_good(self, conn: AsyncConnection, good_id: UUID) -> Good:
        stmt = select(goods_table).where(goods_table.c.id == good_id)
        logger.debug("formed get_good request %s", stmt)

        result = await conn.execute(stmt)

        if result.first:
            good = good_from_row(result.first)
        else:
            logger.info("good with such id not found: %s", good_id)
            raise GoodNotFoundError(good_id)
        
        logger.debug("received user by id %s: %s", good_id, good)
        return good

    async def delete_good(self, conn: AsyncConnection, good_id: UUID):
        stmt = delete(goods_table).where(goods_table.c.id == good_id)
        logger.debug("formed delete_good request %s", stmt)

        await conn.execute(stmt)
        logger.info("executed delete by id %s", good_id)

    async def look_good(self, conn: AsyncConnection, look_filter: LookFilter) -> GoodsList:
        stmt = select(goods_table)
        if look_filter.location:
            stmt = stmt.where(ST_Distance(goods_table.c.location, look_filter.location))
        if look_filter.user_id:
            stmt = stmt.where(goods_table.c.owner_id == look_filter.user_id)
        # also need to add full name search

        logger.debug("formed look_good request: %s", stmt)

        result = await conn.execute(stmt)
        good_list = []
        for row in result:
            good_list.append(good_from_row(row))
        logger.debug("received good list %s by filter %s", good_list, look_filter)
        
        return GoodsList(array=good_list)
