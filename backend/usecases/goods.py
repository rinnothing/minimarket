from uuid import UUID

from model import Good, GoodsList, GoodNotBelongsError, LookFilter

import logging
logger = logging.getLogger(__name__)

class GoodRepo:
    def add_good(self, good: Good) -> Good:
        raise NotImplementedError
    
    def update_good(self, good_id: UUID, good: Good) -> Good:
        raise NotImplementedError
    
    def get_good(self, good_id: UUID) -> Good:
        raise NotImplementedError
    
    def delete_good(self, good_id: UUID):
        raise NotImplementedError
    
    def look_good(self, look_filter: LookFilter) -> GoodsList:
        raise NotImplementedError

class GoodUsecase:
    def __init__(self, good: GoodRepo):
        self.good = good

    def publish_good(self, user_id: UUID, good: Good) -> Good:
        good = good.model_copy(update={"id": None, "owner_id": user_id})

        good = self.good.add_good(good)
        logger.info("published new good %s from user %s", good, user_id)
        return good
    
    def get_good(self, good_id: UUID) -> Good:
        return self.good.get_good(good_id)
    
    def update_good(self, user_id: UUID, good_id: UUID, good: Good) -> Good:
        good = good.model_copy(update={"id": good_id})
        old_good = self.good.get_good(good_id)

        if old_good.owner_id != user_id:
            raise GoodNotBelongsError(good_id, user_id)
        
        good.owner_id = user_id
        good = self.good.update_good(good_id, good)
        logger.info("update info of good %s owned by user %s", good, user_id)
        return good
    
    def delete_good(self, user_id: UUID, good_id: UUID):
        good = self.good.get_good(good_id)

        if good.owner_id != user_id:
            raise GoodNotBelongsError(good_id, user_id)

        self.good.delete_good(good_id)
        logger.info("remove good with id %s owned by user %s", good_id, user_id)

    def look_good(self, filter: LookFilter) -> GoodsList:
        return self.good.look_good(filter)
