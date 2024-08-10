class UsernameAlreadyExistsException(Exception):
    def __init__(self, message="Username already exists"):
        self.message = message
        super().__init__(self.message)

class UsernameDoesNotExistException(Exception):
    def __init__(self, message="Username does not exist"):
        self.message = message
        super().__init__(self.message)

class ExerciseDoesNotExistException(Exception):
    def __init__(self, message="Exercise does not exist", name=None):
        self.message = message
        if name is not None:
            self.message += f" [{name}]"
        super().__init__(self.message)