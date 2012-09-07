from lib import util

import logging
import os

"""
This is the main data class. The deploy method of this class will be called
for all data-* sections specified in the config file.
"""
class Data:
    def __init__(self, name, env, config):
        self.log = logging.getLogger(__name__)

        # required
        self.name = name
        self.env = env
        self.config = config
        self.base_deploy_dir = config.get('global', 'final-deploy-directory')
        self.local_file = config.get(name, 'local-file')
        self.remote_file = config.get(name, 'remote-file')

        # optional
        try:
            self.env_var = config.get(name, 'data-file-environment-var-name')
            self.env_var = self.env_var
        except:
            self.log.debug('%s has no data-file-environment-var-name' % name)
            self.env_var = None

        # other
        self.complete = False
        self.success = False
        self.error = ''

    def _download(self):
        self.log.info('Downloading %s' % self.name)
        rc = util.download_file(self.remote_file,
                                self.base_deploy_dir,
                                self.local_file)
        return rc

    def deploy(self):
        self.log.info('Deploying data: %s' % self.name)
        local_file = os.path.join(self.base_deploy_dir, self.local_file)
        if os.path.exists(local_file):
            self.log.info('%s exists, skipping download.' % self.name)
            return -1
        rc = self._download()
        if self.env_var:
            file_loc = os.path.join(self.base_deploy_dir, self.local_file)
            self.env.update_env_var(self.env_var, file_loc)
        return rc
