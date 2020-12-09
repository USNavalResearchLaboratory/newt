__author__ = 'scmijt'


class NoTargetDefinedException(Exception):
    def __init__(self, *args, **kwargs):
        super(NoTargetDefinedException, self).__init__(*args, **kwargs)


class NoDataFromEdgeException(Exception):
    def __init__(self, *args, **kwargs):
        super(NoDataFromEdgeException, self).__init__(*args, **kwargs)
