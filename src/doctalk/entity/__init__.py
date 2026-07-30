from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DataIngestionConfig:
    '''
    It is a contract for dataingestion block of config.yaml
    the configuration manager fills this in and hand it to the data ingestion component.
    The component, the component never touches the yaml itself.
    '''
    root_dir : Path
    chunk_size : int
    chunk_overlap : int

@dataclass(frozen=True)
class VectorStoreConfig:
    '''
    config for the session-scoped chroma vector store.
    root_dir holds one subfolder per user session.
    embedding_model comes from params.yaml.
    '''
    root_dir: Path
    embedding_model: str

@dataclass(frozen=True)
class RetrieverConfig:
    '''
    config for the retriever. k = how many chunks to pull per query.
    '''
    k: int

@dataclass(frozen=True)
class SummarizeToolConfig:
    '''
    config for the whole-document summarize tool.
    batch_size = how many chunks per map-step summary.
    chat_model + temperature come from params.yaml.
    '''
    batch_size: int
    chat_model: str
    temperature: float