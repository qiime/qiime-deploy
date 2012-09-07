import ConfigParser
import os

def read_config(config_filename):
    if not config_filename:
        config_filename = os.path.join(os.getcwd(), 'etc/app-deploy.conf')
    config = ConfigParser.ConfigParser()
    config.readfp(open(config_filename))
    return config
