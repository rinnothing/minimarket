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
    def add_nonactive(this, user: User) -> User:
        raise NotImplementedError
    
    def activate(this, id: UUID) -> User:
        raise NotImplementedError
    
    def is_mail_used(this, email: NameEmail) -> bool:
        raise NotImplementedError
    
    def is_telegram_used(this, telegram: str) -> bool:
        raise NotImplementedError
    
    def get_user(this, uuid: UUID) -> User:
        raise NotImplementedError
    
    def get_by_username(this, username: str) -> User:
        raise NotImplementedError
    
    def update_user_info(this, uuid: UUID, name: str | None = None, active_time: str | None = None) -> User:
        raise NotImplementedError
    
    def update_user(this, user: User) -> User:
        raise NotImplementedError
    
class GoodRepo:
    def get_good(this, uuid: UUID) -> Good:
        raise NotImplementedError

class MailNotifier:
    def confirm_address(this, email: NameEmail, task_id, args):
        raise NotImplementedError
    
    def ask(this, email: NameEmail, message: str, task_id, args):
        raise NotImplementedError
    
    def notify(this, email: NameEmail, message: Message, time_window: ActiveTime | None = None):
        raise NotImplementedError

class TelegramNotifier:
    def confirm_address(this, telegram: str, task_id, args):
        raise NotImplementedError
    
    def ask(this, email: NameEmail, message: str, task_id, args):
        raise NotImplementedError
    
    def notify(this, telegram: str, message: Message, time_window: ActiveTime | None = None):
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
    def __init__(this, user: UserRepo, good: GoodRepo, mail: MailNotifier, telegram: TelegramNotifier, late_executor: LateExecutor):
        this.user = user
        this.good = good
        this.mail = mail
        this.telegram = telegram
        this.late_executor = late_executor

        def callback_activate(user_id: UUID):
            this.user.activate(user_id)
            logger.info("activated user with id %s", user_id)

        late_executor.register_task(ACTIVATE_CALLBACK, callback_activate)

        def callback_update(user: User):
            this.user.update_user(user)
            logger.info("updated user %s", safe_print_user(user))

        late_executor.register_task(UPDATE_CALLBACK, callback_update)

        def callback_reset_password(user: User):
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(20)) 

            user.hashed_pasword = get_password_hash(password)
            this.user.update_user(user)

            if user.email:
                this.mail.notify(user.email, f"Your new password is {password}")
            elif user.telegram:
                this.telegram.notify(user.telegram, f"Your new password is {password}")
            logger.info("reset password for user %s", user.id)

        late_executor.register_task(RESET_PASSWORD_CALLBACK, callback_reset_password)

        def callback_update_confirmation(args: UpdateConfirmationArguments):
            if args.email:
                args.user.email = args.email

                this.mail.confirm_address(args.email, "Confirm your new confirmation source", UPDATE_CALLBACK, args.user)
            elif args.telegram:
                args.user.telegram = args.telegram
                
                this.telegram.confirm_address(args.telegram, "Confirm your new confirmation source", UPDATE_CALLBACK, args.user)
            logger.info("sent confirmation to the new source for user %s", args.user.id)

        late_executor.register_task(UPDATE_CONFIRMATION_CALLBACK, callback_update_confirmation)

    def register_user(this, user: User, password: str) -> User:
        user = user.model_copy(update={"id": None, "hashed_password": get_password_hash(password), "active": False})
        
        if not user.email and not user.telegram:
            raise NoConfirmationSourceError()
        
        user = this.user.add_nonactive(user)

        if user.email:
            if this.user.is_mail_used(user.email):
                raise ConfirmationInUseError("email", user.email)

            this.mail.confirm_address(user.email, ACTIVATE_CALLBACK, user.id)
        elif user.telegram:
            if this.user.is_telegram_used(user.telegram):
                raise ConfirmationInUseError("telegram", user.telegram)

            this.telegram.confirm_address(user.telegram, ACTIVATE_CALLBACK, user.id)

        logger.info("created unactivated user %s", safe_print_user(user))
        
        return user
    
    def get_user(this, id: UUID) -> User:
        return this.user.get_user(id)
    
    def get_by_username(this, username: str) -> User:
        return this.user.get_by_username(username)
    
    def update_user_info(this, id: UUID, name: str | None = None, active_time: str | None = None) -> User:
        user = this.user.update_user_info(this, id, name, active_time)
        logger.info("updated user %s", safe_print_user(user))
        return user

    def message_owner(this, message: Message):
        message = message.model_copy(update={"recipient": None})
        good = this.good.get_good(message.good_id)

        message.recipient = good.owner_id
        owner = this.user.get_user(good.owner_id)
        
        if owner.email:
            this.mail.notify(owner.email, message, time_window = owner.active_time)
        if owner.telegram:
            this.telegram.notify(owner.telegram, message, time_window = owner.active_time)
        logger.info("sent message %s", message)

    def change_password(this, user_id: UUID, old_password: str, new_password: str):
        user = this.user.get_user(user_id)

        if not verify_password(old_password, user.hashed_pasword):
            raise IncorrectOldPasswordError(old_password)
        
        user.hashed_pasword = get_password_hash(new_password)

        if user.email:
            this.mail.ask(user.email, "Confirm updating your pasword", UPDATE_CALLBACK, user)
        elif user.telegram:
            this.telegram.ask(user.telegram, "Confirm updating your pasword", UPDATE_CALLBACK, user)
        logger.info("sent confirmation for updating the password for user %s", user_id)

    def reset_password(this, username: str):
        user = this.user.get_by_username(username)

        if user.email:
            this.mail.ask(user.email, "Confirm resetting your password", RESET_PASSWORD_CALLBACK, user)
        elif user.telegram:
            this.mail.ask(user.email, "Confirm resetting your password", RESET_PASSWORD_CALLBACK, user)
        logger.info("sent confirmation for resetting the password for user %s", user.id)

    def update_confirmation(this, user_id: UUID, email: NameEmail | None = None, telegram: str | None = None):
        user = this.user.get_user(user_id)

        args = UpdateConfirmationArguments(user, email, telegram)

        if user.email:
            this.mail.ask(user.email, "Confirm updating your confirmation source", UPDATE_CONFIRMATION_CALLBACK, args)
        elif user.telegram:
            this.telegram.notify(user.telegram, "Confirm updating your confirmation source", UPDATE_CONFIRMATION_CALLBACK, args)
        logger.info("sent confirmation to the old source for user %s", user_id)
