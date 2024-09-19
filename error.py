from logger import log


class SynthEcoError(Exception):
    """
    SynthEcoError - Class that can be used as an exeption
    and prints to the proper logging for SynthEco
    """

    def __init__(self, msg=""):
        """
        Instant constructor

        Arguments:
            msg: string for message to give details about the error
        """
        self.msg = msg
        log("ERROR", msg)
        super().__init__(self.msg)
