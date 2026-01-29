class NoConfirmationSourceError(Exception):
    """Exception raised when no confirmation source was provided"""

    def __init__(self):
        super().__init__("Should have at least one confirmation source")

class ConfirmationInUseError(Exception):
    """Exception raised when confirmation is already used
    
    Attributes:
        source -- email or telegram
        value -- address on chosen confirmation source
    """

    def __init__(self, source, value):
        self.source = source
        self.value = value
        super().__init__(f"Address {self.value} on {self.source} is already in use")

class IncorrectOldPasswordError(Exception):
    """Exception raised when provided incorrect old password to change it
    
    Attributes:
        password -- incorrect password given
    """

    def __init__(self, password):
        self.password = password
        super().__init__(f"Old password {self.password}, provided to update it isn't correct")

class GoodNotBelongsError(Exception):
    """Exception raised when trying to change data of good that doesn't belong to user
    
    Attributes:
        good_id -- id of the good
        user_id -- id of the user trying to change data of good
    """

    def __init__(self, good_id, user_id):
        self.good_id = good_id
        self.user_id = user_id
        super().__init__(f"Trying to change data of good {self.good_id} that doesn't belong to user {self.user_id}")
