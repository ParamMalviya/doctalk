from pathlib import Path
'''
Instead of using path in the form strings, which may cause typo, we define it here once and import it wherever needed.
'''
CONFIG_FILE_PATH = Path("config/config.yaml")
PARAMS_FILE_PATH = Path("params.yaml")