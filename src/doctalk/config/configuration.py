from doctalk.constants import CONFIG_FILE_PATH, PARAMS_FILE_PATH
from doctalk.utils.common import read_yaml, create_directories
from doctalk.entity import DataIngestionConfig, VectorStoreConfig, RetrieverConfig, SummarizeToolConfig
from pathlib import Path

class ConfigurationManager:
    '''
    read config.yaml and params.yaml and hand out typed config object per component on request 
    '''
    def __init__(self, config_filepath = CONFIG_FILE_PATH, params_filepath = PARAMS_FILE_PATH):
        # load both yaml into plain dict.
        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        '''
        pull data_ingestion block out of config.yaml, make sure it IS output folder exist and return it as a typed entity
        '''
        config = self.config['data_ingestion']

        create_directories([config['root_dir']])

        data_ingestion_config = DataIngestionConfig(
            root_dir = Path(config['root_dir']),
            chunk_size = config['chunk_size'],
            chunk_overlap = config['chunk_overlap']
        )

        return data_ingestion_config

    def get_vector_store_config(self) -> VectorStoreConfig:
        '''
        vector store paths come from config.yaml, the embedding
        model name comes from params.yaml. combine both into one entity.
        '''
        config = self.config["vector_store"]

        create_directories([config["root_dir"]])

        vector_store_config = VectorStoreConfig(
            root_dir=Path(config["root_dir"]),
            embedding_model=self.params["embedding_model"],
        )

        return vector_store_config

    def get_retriever_config(self) -> RetrieverConfig:
        '''
        how many chunks to retrieve per question
        '''
        config = self.config["retriever"]

        retriever_config = RetrieverConfig(
            k=config["k"],
        )

        return retriever_config

    def get_summarize_tool_config(self) -> SummarizeToolConfig:
        '''
        combine the batch size (config.yaml) with the chat model
        and temperature (params.yaml) into one entity.
        '''
        config = self.config["summarize_tool"]

        summarize_tool_config = SummarizeToolConfig(
            batch_size=config["batch_size"],
            chat_model=self.params["chat_model"],
            temperature=self.params["temperature"],
        )

        return summarize_tool_config