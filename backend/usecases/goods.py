from uuid import UUID

from model import Good, GoodsList, GoodNotBelongsError, LookFilter

class GoodRepo:
    def add_good(this, good: Good) -> Good:
        raise NotImplementedError
    
    def update_good(this, good_id: UUID, good: Good) -> Good:
        raise NotImplementedError
    
    def get_good(this, good_id: UUID) -> Good:
        raise NotImplementedError
    
    def delete_good(this, good_id: UUID):
        raise NotImplementedError
    
    def look_good(this, look_filter: LookFilter) -> GoodsList:
        raise NotImplementedError

class GoodUsecase:
    def __init__(this, good: GoodRepo):
        this.good = good

    def publish_good(this, user_id: UUID, good: Good) -> Good:
        good = good.model_copy(update={"id": None, "owner_id": user_id})

        return this.good.add_good(good)
    
    def get_good(this, good_id: UUID) -> Good:
        return this.good.get_good(good_id)
    
    def update_good(this, user_id: UUID, good_id: UUID, good: Good) -> Good:
        good = good.model_copy(update={"id": good_id})
        old_good = this.good.get_good(good_id)

        if old_good.owner_id != user_id:
            raise GoodNotBelongsError(good_id, user_id)
        
        good.owner_id = user_id
        return this.good.update_good(good_id, good)
    
    def delete_good(this, user_id: UUID, good_id: UUID):
        good = this.good.get_good(good_id)

        if good.owner_id != user_id:
            raise GoodNotBelongsError(good_id, user_id)

        this.good.delete_good(good_id)

    def look_good(this, filter: LookFilter) -> GoodsList:
        return this.good.look_good(filter)
