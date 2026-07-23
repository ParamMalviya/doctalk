from doctalk.constants import CONFIG_FILE_PATH, PARAMS_FILE_PATH
from doctalk.utils.common import read_yaml, create_directories
from doctalk.entity import DataIngestionConfig
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