from typing import Any
from uuid import UUID

import logging
logger = logging.getLogger(__name__)

class TaskArgumentStorage:
    def put(action_id, args) -> UUID:
        raise NotImplementedError
    
    # returns action_id and args of the said task
    def get(task_id: UUID) -> tuple[Any, Any]:
        raise NotImplementedError

class ActionNotExistsError(Exception):
    """Exception raised when action with such id doesn't exist
    
    Attributes:
        action_id -- given action id
    """
    def __init__(this, action_id):
        this.action_id = action_id
        super().__init__(f"Action with id {this.action_id} doesn't exist")

class LateExecutor:
    """
    This class allows to store action that should be executed later
    """
    def __init__(this, arg_storage: TaskArgumentStorage):
        this.tasks_action_dict = dict()
        this.arg_storage = arg_storage

    def register_task(this, action_id, action):
        this.tasks_action_dict[action_id] = action
        logger.debug("registered action with id %s", action_id)

    def put_task(this, action_id, args) -> UUID:
        id = this.arg_storage.put(action_id, args)
        logger.debug("put new task with aciton_id = %s, id = %s and args = %s", action_id, id, args)
        return id
    
    def execute_task(this, task_id):
        action_id, args = this.arg_storage.get(task_id)

        if action_id not in this.tasks_action_dict:
            logger.error("action %s not found", action_id)
            raise ActionNotExistsError(action_id)

        action_func = this.tasks_action_dict[action_id]
        action_func(args)
        logger.debug("executed task %s of action %s with args %s", task_id, action_id, args)
