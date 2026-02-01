from uuid import UUID
import secrets
import string

from pydantic import NameEmail, BaseModel

from model import User, Good, Message, ActiveTime, NoConfirmationSourceError, ConfirmationInUseError, IncorrectOldPasswordError, safe_print_user

from utils.security import get_password_hash, verify_password

from utils.late_executor import LateExecutor

import logging
logger = logging.getLogger(__name__)

class UserRepo:
    def add_nonactive(self, user: User) -> User:
        raise NotImplementedError
    
    def activate(self, id: UUID) -> User:
        raise NotImplementedError
    
    def is_mail_used(self, email: NameEmail) -> bool:
        raise NotImplementedError
    
    def is_telegram_used(self, telegram: str) -> bool:
        raise NotImplementedError
    
    def get_user(self, uuid: UUID) -> User:
        raise NotImplementedError
    
    def get_by_username(self, username: str) -> User:
        raise NotImplementedError
    
    def update_user_info(self, uuid: UUID, name: str | None = None, active_time: str | None = None) -> User:
        raise NotImplementedError
    
    def update_user(self, user: User) -> User:
        raise NotImplementedError
    
class GoodRepo:
    def get_good(self, uuid: UUID) -> Good:
        raise NotImplementedError

class MailNotifier:
    def confirm_address(self, email: NameEmail, task_id, args):
        raise NotImplementedError
    
    def ask(self, email: NameEmail, message: str, task_id, args):
        raise NotImplementedError
    
    def notify(self, email: NameEmail, message: Message, time_window: ActiveTime | None = None):
        raise NotImplementedError

class TelegramNotifier:
    def confirm_address(self, telegram: str, task_id, args):
        raise NotImplementedError
    
    def ask(self, telegram: str, message: str, task_id, args):
        raise NotImplementedError
    
    def notify(self, telegram: str, message: Message, time_window: ActiveTime | None = None):
        raise NotImplementedError

ACTIVATE_CALLBACK = "callback_activate"
UPDATE_CALLBACK = "callback_update"
RESET_PASSWORD_CALLBACK = "callback_reset_password"
UPDATE_CONFIRMATION_CALLBACK = "callback_update_confirmation"

class UpdateConfirmationArguments(BaseModel):
    user: User
    email: NameEmail | None = None
    telegram: str | None = None

class UserUsecase:
    def __init__(self, user: UserRepo, good: GoodRepo, mail: MailNotifier, telegram: TelegramNotifier, late_executor: LateExecutor):
        self.user = user
        self.good = good
        self.mail = mail
        self.telegram = telegram
        self.late_executor = late_executor

        def callback_activate(user_id: UUID):
            self.user.activate(user_id)
            logger.info("activated user with id %s", user_id)

        late_executor.register_task(ACTIVATE_CALLBACK, callback_activate)

        def callback_update(user: User):
            self.user.update_user(user)
            logger.info("updated user %s", safe_print_user(user))

        late_executor.register_task(UPDATE_CALLBACK, callback_update)

        def callback_reset_password(user: User):
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(20)) 

            user.hashed_pasword = get_password_hash(password)
            self.user.update_user(user)

            if user.email:
                self.mail.notify(user.email, f"Your new password is {password}")
            elif user.telegram:
                self.telegram.notify(user.telegram, f"Your new password is {password}")
            logger.info("reset password for user %s", user.id)

        late_executor.register_task(RESET_PASSWORD_CALLBACK, callback_reset_password)

        def callback_update_confirmation(args: UpdateConfirmationArguments):
            if args.email:
                args.user.email = args.email

                self.mail.confirm_address(args.email, "Confirm your new confirmation source", UPDATE_CALLBACK, args.user)
            elif args.telegram:
                args.user.telegram = args.telegram
                
                self.telegram.confirm_address(args.telegram, "Confirm your new confirmation source", UPDATE_CALLBACK, args.user)
            logger.info("sent confirmation to the new source for user %s", args.user.id)

        late_executor.register_task(UPDATE_CONFIRMATION_CALLBACK, callback_update_confirmation)

    def register_user(self, user: User, password: str) -> User:
        user = user.model_copy(update={"id": None, "hashed_password": get_password_hash(password), "active": False})
        
        if not user.email and not user.telegram:
            raise NoConfirmationSourceError()
        
        user = self.user.add_nonactive(user)

        if user.email:
            if self.user.is_mail_used(user.email):
                raise ConfirmationInUseError("email", user.email)

            self.mail.confirm_address(user.email, ACTIVATE_CALLBACK, user.id)
        elif user.telegram:
            if self.user.is_telegram_used(user.telegram):
                raise ConfirmationInUseError("telegram", user.telegram)

            self.telegram.confirm_address(user.telegram, ACTIVATE_CALLBACK, user.id)

        logger.info("created unactivated user %s", safe_print_user(user))
        
        return user
    
    def get_user(self, id: UUID) -> User:
        return self.user.get_user(id)
    
    def get_by_username(self, username: str) -> User:
        return self.user.get_by_username(username)
    
    def update_user_info(self, id: UUID, name: str | None = None, active_time: str | None = None) -> User:
        user = self.user.update_user_info(self, id, name, active_time)
        logger.info("updated user %s", safe_print_user(user))
        return user

    def message_owner(self, message: Message):
        message = message.model_copy(update={"recipient": None})
        good = self.good.get_good(message.good_id)

        message.recipient = good.owner_id
        owner = self.user.get_user(good.owner_id)
        
        if owner.email:
            self.mail.notify(owner.email, message, time_window = owner.active_time)
        if owner.telegram:
            self.telegram.notify(owner.telegram, message, time_window = owner.active_time)
        logger.info("sent message %s", message)

    def change_password(self, user_id: UUID, old_password: str, new_password: str):
        user = self.user.get_user(user_id)

        if not verify_password(old_password, user.hashed_pasword):
            raise IncorrectOldPasswordError(old_password)
        
        user.hashed_pasword = get_password_hash(new_password)

        if user.email:
            self.mail.ask(user.email, "Confirm updating your pasword", UPDATE_CALLBACK, user)
        elif user.telegram:
            self.telegram.ask(user.telegram, "Confirm updating your pasword", UPDATE_CALLBACK, user)
        logger.info("sent confirmation for updating the password for user %s", user_id)

    def reset_password(self, username: str):
        user = self.user.get_by_username(username)

        if user.email:
            self.mail.ask(user.email, "Confirm resetting your password", RESET_PASSWORD_CALLBACK, user)
        elif user.telegram:
            self.mail.ask(user.email, "Confirm resetting your password", RESET_PASSWORD_CALLBACK, user)
        logger.info("sent confirmation for resetting the password for user %s", user.id)

    def update_confirmation(self, user_id: UUID, email: NameEmail | None = None, telegram: str | None = None):
        user = self.user.get_user(user_id)

        args = UpdateConfirmationArguments(user, email, telegram)

        if user.email:
            self.mail.ask(user.email, "Confirm updating your confirmation source", UPDATE_CONFIRMATION_CALLBACK, args)
        elif user.telegram:
            self.telegram.ask(user.telegram, "Confirm updating your confirmation source", UPDATE_CONFIRMATION_CALLBACK, args)
        logger.info("sent confirmation to the old source for user %s", user_id)
