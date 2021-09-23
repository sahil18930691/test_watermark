import logging

logFormatter = logging.Formatter("[%(asctime)s] [%(process)d] [%(levelname)s]  %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)