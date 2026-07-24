import sys
from pathlib import Path

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from doctalk.entity import DataIngestionConfig
from doctalk.logger import logger
from doctalk.exception import CustomException


class DataIngestion:
    '''
    takes an uploaded pdf and turns it into a list of chunks
    ready for embedding. does two jobs:
      1. read the pdf into Document objects, one per page
      2. split those into smaller overlapping chunks
    '''

    def __init__(self, config: DataIngestionConfig):
        # the typed config object from ConfigurationManager.
        # this component never reads yaml itself
        self.config = config

    def load_pdf(self, file_path: Path) -> list[Document]:
        '''
        read a pdf page by page and wrap each page in a Document,
        keeping the filename and page number as metadata so i can
        show citations later
        '''
        try:
            reader = PdfReader(str(file_path))
            documents = []

            # start=1 so pages are numbered like a human reads them, not from 0
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""

                # skip blank pages, e.g. scanned images with no text layer
                if text.strip() == "":
                    logger.info(f"skipped empty page {page_number} in {file_path.name}")
                    continue

                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": file_path.name, "page": page_number},
                    )
                )

            logger.info(f"loaded {len(documents)} pages from {file_path.name}")
            return documents

        except Exception as e:
            raise CustomException(e, sys) from e

    def split_documents(self, documents: list[Document]) -> list[Document]:
        '''
        cut the page Documents into smaller overlapping chunks.
        metadata carries over automatically to every chunk
        '''
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
            )

            chunks = splitter.split_documents(documents)
            logger.info(f"split into {len(chunks)} chunks")
            return chunks

        except Exception as e:
            raise CustomException(e, sys) from e

    def run(self, file_path: Path) -> list[Document]:
        '''
        the whole ingestion job in one call: pdf in, chunks out
        '''
        documents = self.load_pdf(file_path)
        chunks = self.split_documents(documents)
        return chunks