import sys
import os
from pathlib import Path
import yaml
from ensure import ensure_annotations

from doctalk.logger import logger
from doctalk.exception import CustomException

@ensure_annotations
def read_yaml(path_to_yaml: Path) -> dict:
    '''
    it reads path to a yaml file and returns a dictionary
    '''
    try:
        
        with open(path_to_yaml) as yaml_file:
            content = yaml.safe_load(yaml_file)
            logger.info(f"yaml file loaded: {path_to_yaml}")
            return content

    except Exception as e:
        raise CustomException(e,sys) from e
    
@ensure_annotations
def create_directories(path_to_directories: list, verbose = True):
    '''
    make each folder in the list
    '''
    for path in path_to_directories:
        os.makedirs(path, exist_ok=True)

        if verbose:
            logger.info(f"created directory at: {path}")