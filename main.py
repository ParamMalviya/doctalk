from doctalk.logger import setup_logging, logger


# This congigures logging once at the starting, before anything else
setup_logging()

if __name__ == "__main__":
    logger.info("DocTalk starting up")
    logger.info("logging is configured and working")