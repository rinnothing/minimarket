from uuid import UUID

from fastapi import APIRouter

from utils.late_executor import LateExecutor

def init(late_executor: LateExecutor) -> APIRouter:
    router = APIRouter(prefix="/confirm", tags=["confirm"])

    @router.get("/{confirmation_id}")
    def confirm(confirmation_id: UUID):
        # don't know what to return, maybe just redirect to some other page
        late_executor.execute_task(confirmation_id)

    return router