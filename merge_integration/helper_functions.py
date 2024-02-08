import logging


file = "apiLog"


def api_log(level=logging.DEBUG, msg=""):
    logging.basicConfig(level=level, filename=file, filemode='a', format='%(asctime)s [%(levelname)s] %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p', encoding='utf-8')
    logging.log(level, msg)