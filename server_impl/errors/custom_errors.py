from connexion import ProblemException
from werkzeug.exceptions import BadRequest, NotFound, Conflict


class EBadRequest(ProblemException, BadRequest):
    def __init__(self, title='Bad Request'):
        super(EBadRequest, self).__init__(title=title)


class ENotFound(ProblemException, NotFound):
    def __init__(self, title='Not Found'):
        super(ENotFound, self).__init__(title=title)


class EConflict(ProblemException, Conflict):
    def __init__(self, title='Conflict'):
        super(EConflict, self).__init__(title=title)
