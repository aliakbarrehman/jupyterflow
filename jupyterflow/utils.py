import os

import yaml
import pkgutil
import base64


def _get_config_file_path():
    home = os.environ['HOME']
    CONFIG_FILE = os.path.join(home, '.jupyterflow.yaml')
    return os.environ.get('JUPYTERFLOW_CONFIG_FILE', CONFIG_FILE)

def create_config():
    data = pkgutil.get_data(__name__, "templates/jupyterflow.yaml")

    CONFIG_FILE = _get_config_file_path()
    with open(CONFIG_FILE, 'wt') as f:
        f.write(data.decode('utf-8'))


def load_config():
    CONFIG_FILE = _get_config_file_path()
    
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            conf = yaml.safe_load(f)
            if conf is None:
                return {}
            return conf
    return {}


def hanle_exception():
    pass

def handle_exception(error):
    print(error)
    raise Exception(error)

def check_null_or_empty(variable):
    if (variable is None or str(variable) == ''):
        return True
    return False

def encode_base64(value):
    base64_bytes = base64.b64encode(value.encode("ascii"))
    return base64_bytes.decode("ascii")

def decode_base64(value):
    base64_bytes = base64.b64decode(value.encode("ascii"))
    return base64_bytes.decode("ascii")