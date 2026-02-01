from pydantic import NameEmail

import time

from usecases.users import TelegramNotifier, MailNotifier, UserRepo
from usecases.goods import GoodRepo
from utils.late_executor import LateExecutor

from model import Message, ActiveTime

from config import config


import logging
logger = logging.getLogger(__name__)

CONFIRM_PREFIX = "/confirm/"

def get_url(late_executor: LateExecutor, task_id, args) -> str:
    id = late_executor.put_task(task_id, args)
    return f"{config.domain}{CONFIRM_PREFIX}{id}"

class TWriter:
    def message(text: str, telegram: str):
        raise NotImplementedError
    
    def message_later(text: str, telegram: str, eta):
        raise NotImplementedError

class TNotifierUsecase(TelegramNotifier):
    def __init__(self, twriter: TWriter, good_repo: GoodRepo, user_repo: UserRepo, late_executor: LateExecutor):
        self.twriter = twriter
        self.good_repo = good_repo
        self.user_repo = user_repo
        self.late_executor = late_executor

    def confirm_address(self, telegram: str, task_id, args):
        url = get_url(self.late_executor, task_id, args)
        self.twriter.message(f"Please, follow the link to confirm your telegram address: {url}", telegram)

    def ask(self, telegram: str, message: str, task_id, args):
        url = get_url(self.late_executor, task_id, args)
        self.twriter.message(f"Please, follow the link to \"{message}\": {url}", telegram)

    def notify(self, telegram: str, message: Message, time_window: ActiveTime | None = None):
        # hours are stored in gmt format in database, so it's frontend's responsibility to convert them to user time
        hour = time.gmtime(time.time()).tm_hour
        to_time = time_window.from_hour
        if time_window.to_hour <= time_window.from_hour:
            to_time += 24
        
        if hour < time_window.from_hour:
            hour += 24

        good = self.good_repo.get_good(message.good_id)
        user = self.user_repo.get_user(message.sender)
        message = f"New message on {good.name} topic received from {user.name}:\n" \
                  f"{message.message}\n" \
                  f"Contact him on: {message.contact_info}"
        
        if time_window.from_hour <= hour and hour <= to_time:
            self.twriter.message(message, telegram)
        else:
            eta = (hour - 24 - time_window.from_hour) * 3600
            self.twriter.message_later(message, telegram, eta)

class MWriter:
    def message(text: str, email: NameEmail):
        raise NotImplementedError
    
    def message_later(text: str, email: NameEmail, eta):
        raise NotImplementedError

class MNotifierUsecase(MailNotifier):
    def __init__(self, mwriter: MWriter, good_repo: GoodRepo, user_repo: UserRepo, late_executor: LateExecutor):
        self.mwriter = mwriter
        self.good_repo = good_repo
        self.user_repo = user_repo
        self.late_executor = late_executor

    def confirm_address(self, email: NameEmail, task_id, args):
        url = get_url(self.late_executor, task_id, args)
        self.mwriter.message(f"Please, follow the link to confirm your telegram address: {url}", email)

    def ask(self, email: NameEmail, message: str, task_id, args):
        url = get_url(self.late_executor, task_id, args)
        self.mwriter.message(f"Please, follow the link to \"{message}\": {url}", email)

    def notify(self, email: NameEmail, message: Message, time_window: ActiveTime | None = None):
        # hours are stored in gmt format in database, so it's frontend's responsibility to convert them to user time
        hour = time.gmtime(time.time()).tm_hour
        to_time = time_window.from_hour
        if time_window.to_hour <= time_window.from_hour:
            to_time += 24
        
        if hour < time_window.from_hour:
            hour += 24

        good = self.good_repo.get_good(message.good_id)
        user = self.user_repo.get_user(message.sender)
        message = f"New message on {good.name} topic received from {user.name}:\n" \
                  f"{message.message}\n" \
                  f"Contact him on: {message.contact_info}"
        
        if time_window.from_hour <= hour and hour <= to_time:
            self.mwriter.message(message, email)
        else:
            eta = (hour - 24 - time_window.from_hour) * 3600
            self.mwriter.message_later(message, email, eta)
