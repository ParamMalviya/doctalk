import sys
from pathlib import Path

from langchain_core.documents import Document

from doctalk.config.configuration import ConfigurationManager
from doctalk.components.data_ingestion import DataIngestion
from doctalk.logger import logger
from doctalk.exception import CustomException


STAGE_NAME = "Data Ingestion"


class IngestionPipeline:
    '''
    stage 1: take a pdf and turn it into chunks.
    reads config once when this object is built, then reuses it,
    so the fastapi route can make one pipeline and call run() per upload.
    later this stage will also embed the chunks into the session vector store.
    '''

    def __init__(self):
        try:
            config_manager = ConfigurationManager()
            self.config = config_manager.get_data_ingestion_config()
            self.data_ingestion = DataIngestion(config=self.config)

        except Exception as e:
            raise CustomException(e, sys) from e

    def run(self, file_path: Path) -> list[Document]:
        '''
        pdf path in, list of chunks out
        '''
        try:
            chunks = self.data_ingestion.run(file_path)
            return chunks

        except Exception as e:
            raise CustomException(e, sys) from e


if __name__ == "__main__":
    # lets me test this stage on its own from the terminal,
    # without fastapi or the notebook
    from doctalk.logger import setup_logging

    setup_logging()

    try:
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")

        pipeline = IngestionPipeline()
        chunks = pipeline.run(Path("eval/test_document.pdf"))

        logger.info(f">>>>>> stage {STAGE_NAME} completed, {len(chunks)} chunks <<<<<<")

    except Exception as e:
        logger.exception(e)
        raise