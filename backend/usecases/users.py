from uuid import UUID
import secrets
import string

from pydantic import NameEmail

from model import User, Good, Message, ActiveTime, NoConfirmationSourceError, ConfirmationInUseError, IncorrectOldPasswordError

from utils.security import get_password_hash, verify_password

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
    def confirm_address(this, email: NameEmail, callback):
        raise NotImplementedError
    
    def ask(this, email: NameEmail, message: str, callback):
        raise NotImplementedError
    
    def notify(this, email: NameEmail, message: Message, time_window: ActiveTime | None = None):
        raise NotImplementedError

class TelegramNotifier:
    def confirm_address(this, telegram: str, callback):
        raise NotImplementedError
    
    def ask(this, email: NameEmail, message: str, callback):
        raise NotImplementedError
    
    def notify(this, telegram: str, message: Message, time_window: ActiveTime | None = None):
        raise NotImplementedError

class UserUsecase:
    def __init__(this, user: UserRepo, good: GoodRepo, mail: MailNotifier, telegram: TelegramNotifier):
        this.user = user
        this.good = good
        this.mail = mail
        this.telegram = telegram

    def register_user(this, user: User, password: str) -> User:
        user = user.model_copy(update={"id": None, "hashed_password": get_password_hash(password), "active": False})
        
        if not user.email and not user.telegram:
            raise NoConfirmationSourceError()
        
        user = this.user.add_nonactive(user)

        if user.email:
            if this.user.is_mail_used(user.email):
                raise ConfirmationInUseError("email", user.email)
            
            # replace callback with something different
            # now it's just a placeholder for the action
            def callback_mail():
                this.user.activate(user.id)

            this.mail.confirm_address(user.email, callback_mail)
        elif user.telegram:
            if this.user.is_telegram_used(user.telegram):
                raise ConfirmationInUseError("telegram", user.telegram)
            
            # replace callback with something different
            # now it's just a placeholder for the action
            def callback_telegram():
                this.user.activate(user.id)

            this.telegram.confirm_address(user.telegram, callback_telegram)
        
        return user
    
    def get_user(this, id: UUID) -> User:
        return this.user.get_user(id)
    
    def update_user_info(this, id: UUID, name: str | None = None, active_time: str | None = None) -> User:
        return this.user.update_user_info(this, id, name, active_time)

    def message_owner(this, message: Message):
        message = message.model_copy(update={"recipient": None})
        good = this.good.get_good(message.good_id)

        message.recipient = good.owner_id
        owner = this.user.get_user(good.owner_id)
        
        if owner.email:
            this.mail.notify(owner.email, message, time_window = owner.active_time)
        if owner.telegram:
            this.telegram.notify(owner.telegram, message, time_window = owner.active_time)

    def change_password(this, user_id: UUID, old_password: str, new_password: str):
        user = this.user.get_user(user_id)

        if not verify_password(old_password, user.hashed_pasword):
            raise IncorrectOldPasswordError(old_password)
        
        user.hashed_pasword = get_password_hash(new_password)
        
        def callback():
            this.user.update_user(user)

        if user.email:
            this.mail.ask(user.email, "Confirm updating your pasword", callback)
        elif user.telegram:
            this.telegram.ask(user.telegram, "Confirm updating your pasword", callback)

    def reset_password(this, username: str):
        user = this.user.get_by_username(username)

        def callback():
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(20)) 

            user.hashed_pasword = get_password_hash(password)
            this.user.update_user(user)

            if user.email:
                this.mail.notify(user.email, f"Your new password is {password}")
            elif user.telegram:
                this.mail.notify(user.telegram, f"Your new password is {password}")

        if user.email:
            this.mail.ask(user.email, "Confirm resetting your password", callback)
        elif user.telegram:
            this.mail.ask(user.email, "Confirm resetting your password", callback)

    def update_confirmation(this, user_id: UUID, email: NameEmail | None = None, telegram: str | None = None):
        user = this.user.get_user(user_id)

        def callback():
            if email:
                user.email = email

                def callback_mail():
                    this.user.update_user(user)

                this.mail.confirm_address(email, "Confirm your new confirmation source", callback_mail)
            elif telegram:
                user.telegram = telegram

                def callback_telegram():
                    this.user.update_user(user)
                
                this.telegram.confirm_address(telegram, "Confirm your new confirmation source", callback_telegram)

        if user.email:
            this.mail.ask(user.email, "Confirm updating your confirmation source", callback)
        elif user.telegram:
            this.telegram.notify(user.telegram, "Confirm updating your confirmation source", callback)
