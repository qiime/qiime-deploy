from lib import custom
from lib import util

import commands
import logging
import os
import shutil
import tempfile

"""
The main application class, responsible for getting an application's config
values and deploying the application. If a new build-type is added to
app-deploy then this class must be modified to support it.
"""
class Application:
    def __init__(self, 
                 name, 
                 env, 
                 config, 
                 custom_py_exe=None,
                 remove_repos=False):
        self.log = logging.getLogger(__name__)

        # required
        self.name = name
        self.env = env
        self.config = config
        if custom_py_exe:
            self.py_exe = custom_py_exe
        else:
            self.py_exe = 'python'
        self.remove_repos = remove_repos

        base_deploy_dir = config.get('global', 'final-deploy-directory')
        base_deploy_dir = os.path.expanduser(base_deploy_dir)
        self.base_deploy_dir = os.path.abspath(base_deploy_dir)

        self.version = config.get(name, 'version')
        self.build_type = config.get(name, 'build-type')

        try:
            self.release_location = config.get(name, 'release-location')
            self.deploy_type = 'release'
        except:
            self.log.debug('%s has no release-location' % name)
            self.release_location = None
        try:
            self.release_file_name = config.get(name, 'release-file-name')
        except:
            self.log.debug('%s has no release-file-name' % name)
            self.release_file_name = None
        try:
            self.repository_type = config.get(name, 'repository-type')
        except:
            self.log.debug('%s has no repository-type' % name)
            self.repository_type = None
        try:
            self.repository_location = config.get(name, 'repository-location')
            self.deploy_type = 'repository'
        except:
            self.log.debug('%s has no repository-location' % name)
            self.repository_location = None
        try:
            self.repository_local_name = config.get(name, 'repository-local-name')
        except:
            self.log.debug('%s has no repository-local-name' % name)
            self.repository_local_name = None
        try:
            self.repository_options = config.get(name, 'repository-options')
        except:
            self.log.debug('%s has no repository-options' % name)
            self.repository_options = ""

        self.repo_version = None
        if self.deploy_type == 'repository':
            repo_location = self.repository_location
            if self.repository_type == 'svn':
                self.repo_version = util.get_svn_repository_version(repo_location)
            elif self.repository_type == 'git':
                self.repo_version = util.get_git_repository_version(repo_location)

            if not self.repo_version:
                self.repo_version = 'unknown-repo-version'
            self.deploy_name = self.name + '-' + \
                               self.version + '-' + \
                               self.deploy_type + '-' + \
                               self.repo_version
        else:
            self.deploy_name = self.name + '-' + \
                               self.version + '-' + \
                               self.deploy_type
        self.deploy_dir = os.path.join(self.base_deploy_dir, self.deploy_name)

        try:
            self.py_site_pkgs = config.get(name, 'deploy-in-python-site-packages')
            if self.py_site_pkgs.strip() == 'yes':
                self.log.debug('%s is deploying in python site-packages' % name)
                self.py_site_pkgs = True
            else:
                self.log.debug('%s is not deploying in python site-packages' % name)
                self.py_site_pkgs = False
        except:
            self.log.debug('%s is not deploying in python site-packages' % name)
            self.py_site_pkgs = False

        # optional
        if self.deploy_type == 'release':
            try:
                self.skip_unzipped_name = config.get(name, 'skip-unzipped-name')
                if self.skip_unzipped_name == 'yes':
                    self.skip_unzipped_name = True
                else:
                    self.skip_unzipped_name = False
            except:
                self.skip_unzipped_name = False

            if not self.skip_unzipped_name:
                try:
                    self.unzipped_name = config.get(name, 'unzipped-name')
                except:
                    self.log.debug('%s has no unzipped-name' % name)
                    self.log.debug('Attempting to determine the unzipped name.')
                    new_name = None
                    if self.release_file_name.endswith('.tar.gz'):
                        new_name = self.release_file_name.replace('.tar.gz', '')
                    elif self.release_file_name.endswith('.tgz'):
                        new_name = self.release_file_name.replace('.tgz', '')
                    elif self.release_file_name.endswith('.zip'):
                        new_name = self.release_file_name.replace('.zip', '')
                    self.unzipped_name = new_name
            else:
                self.unzipped_name = None
        else:
            self.skip_unzipped_name = True
            self.unzipped_name = None

        try:
            self.ac_config_opts = config.get(name, 'autoconf-configure-options')
        except:
            self.log.debug('%s has no autoconf-configure-options' % name)
            self.ac_config_opts = None

        try:
            self.ac_make_opts = config.get(name, 'autoconf-make-options')
        except:
            self.log.debug('%s has no autoconf-make-options' % name)
            self.ac_make_opts = None

        try:
            self.make_opts = config.get(name, 'make-options')
        except:
            self.log.debug('%s has no make-options' % name)
            self.make_opts = None

        try:
            self.make_install_opts = config.get(name, 'make-install-options')
        except:
            self.log.debug('%s has no make-install-options' % name)
            self.make_install_opts = None

        try:
            self.c_compile_opts = config.get(name, 'c-file-compile-options')
        except:
            self.log.debug('%s has no c-file-compile-options' % name)
            self.c_compile_opts = None

        try:
            self.cpp_compile_opts = config.get(name, 'cpp-file-compile-options')
        except:
            self.log.debug('%s has no cpp-file-compile-options' % name)
            self.cpp_compile_opts = None

        try:
            self.exe_name = config.get(name, 'exe-name')
        except:
            self.log.debug('%s has no exe-name' % name)
            self.exe_name = None

        try:
            self.py_build_opts = config.get(name, 'python-build-options')
        except:
            self.log.debug('%s has no python-build-options' % name)
            self.py_build_opts = None
            
        try:
            self.py_install_opts = config.get(name, 'python-install-options')
        except:
            self.log.debug('%s has no python-install-options' % name)
            self.py_install_opts = None

        try:
            self.post_bash_cmds = config.get(name, 'post-bash-commands')
        except:
            self.log.debug('%s has no post-bash-commands' % name)
            self.post_bash_cmds = None

        try:
            rel_path_dir = config.get(name, 'relative-directory-add-to-path')
        except:
            self.log.debug('%s has no relative-directory-add-to-path' % name)
            self.rel_path_dirs = []
            rel_path_dir = None

        if rel_path_dir:
            rel_path_dir = rel_path_dir.split(',')
            rel_paths = [os.path.join(self.deploy_dir, x.strip()) for x in rel_path_dir]
            self.rel_path_dirs = rel_paths

        try:
            env_vars = config.get(name, 'set-environment-variables-deploypath')
        except:
            self.log.debug('%s has no set-environment-variables-deploypath' % name)
            self.env_vars = []
            env_vars = None

        if env_vars:
            env_vars_split = env_vars.split(',')
            self.env_vars = []
            for env_var in env_vars_split:
                env_var = env_var.strip()
                env_name = env_var.split('=')[0]
                env_value = env_var.split('=')[1]
                new_env_value = os.path.join(self.deploy_dir, env_value)
                new_env_var = env_name + '=' + new_env_value
                self.env_vars.append(new_env_var)

        try:
            env_var_values = config.get(name, 'set-environment-variables-value')
        except:
            self.log.debug('%s has no set-environment-variables-value' % name)
            self.env_var_values = []
            env_var_values = None

        if env_var_values:
            env_var_values_split = env_var_values.split(',')
            env_var_values_split = [x.strip() for x in env_var_values_split]
            for env_var_value in env_var_values_split:
                self.log.debug('Appending %s to env_vars' % env_var_value)
                self.env_vars.append(env_var_value)

        try:
            self.cp_src_dir = config.get(name, 'copy-source-to-final-deploy')
            if self.cp_src_dir == 'yes':
                self.cp_src_dir = True
            else:
                self.cp_src_dir = False
        except:
            self.cp_src_dir = False

        try:
            self.deps = config.get(name, 'deps').strip()
            if self.deps == 'None':
                self.log.debug('%s has no deps' % name)
                self.deps = None
            else:
                if self.deps:
                    self.deps = self.deps.split(',')
                    self.deps = [x.strip() for x in self.deps]
        except:
            self.log.debug('%s has no deps' % name)
            self.deps = None

        # other
        self.complete = False
        self.success = False
        self.error = ''
        try:
            tmp_base = config.get('global', 'tmp-directory').strip()
            tmp_base = os.path.expanduser(tmp_base)
            tmp_base = os.path.abspath(tmp_base)
        except:
            tmp_base = None
        self.tmp_dir = tempfile.mkdtemp(dir=tmp_base)

    def _download(self):
        self.log.info('Downloading %s' % self.name)
        download_release = True
        rc = 1
        if self.deploy_type == 'repository':
            download_release = False

        if download_release:
            rc = util.download_file(self.release_location,
                                    self.tmp_dir,
                                    self.release_file_name)
        else:
            if self.repository_type == 'svn':
                rc = util.svn_checkout(self.repository_location,
                                       self.tmp_dir,
                                       self.repository_local_name,
                                       self.repository_options)
            elif self.repository_type == 'git':
                rc = util.git_clone(self.repository_location,
                                    self.tmp_dir,
                                    self.repository_local_name,
                                    self.repository_options)
                                   
        return rc

    def _copy_dir(self, setup_dir):
        self.log.debug('Copying %s to final location.' % self.name)
        os.rmdir(self.deploy_dir)
        rc = util.copytree(setup_dir, self.deploy_dir)
        if rc != 0:
            self.log.error('Problem copy directory for %s.' % self.name)
            return 1
        else:
            self.log.info('Successfully copied %s directory.' % self.name)
        return 0

    def _deploy_autoconf(self, setup_dir):
        rc = util.gnu_autoconf(self.name, 
                               setup_dir,
                               self.deploy_dir,
                               self.ac_config_opts,
                               self.ac_make_opts)
        if rc != 0:
            self.log.error('Problem deploying %s.' % self.name)
            return 1
        else:
            self.log.info('Successfully built %s.' % self.name)
        return 0

    def _guess_site_packages(self):
        self.log.debug('Guessing site-packages directory for %s' % self.name)
        version_str = '%s -c "import sys; print sys.version_info[:2]"' % self.py_exe
        os.chdir(self.deploy_dir)
        self.log.debug('EXE: %s' % version_str)
        (vStatus, vOut) = commands.getstatusoutput(version_str)
        if vStatus != 0:
            self.log.debug('Problem guessing python site-package directory.')
        else:
            vOut = vOut.lstrip('(')
            vOut = vOut.rstrip(')')
            vOut = vOut.split(',')
            major = int(vOut[0].strip())
            minor = int(vOut[1].strip())
            full_path = os.path.join(self.deploy_dir, 'lib')
            full_path = os.path.join(full_path, 'python%s.%s' % (major, minor))
            full_path = os.path.join(full_path, 'site-packages')
            return full_path
        return None

    def _deploy_python_distutils(self, setup_dir):
        install_opts = None
        if self.py_install_opts:
            split_opts = self.py_install_opts.split()
            for c_opt in split_opts:
                c_opt_split = c_opt.split('=')
                if len(c_opt_split) > 1:
                    if (c_opt_split[1].endswith('/')) and \
                       (not c_opt_split[1].startswith('/')):
                        new_path = os.path.join(self.deploy_dir,
                                                c_opt_split[1])
                        new_opt = ' ' + c_opt_split[0] + '=' + new_path
                        if not install_opts:
                            install_opts = new_opt
                        else:
                            install_opts += new_opt
                    else:
                        if not install_opts:
                            install_opts = c_opt
                        else:
                            install_opts += ' ' + c_opt
                else:
                    if not install_opts:
                        install_opts = c_opt
                    else:
                        install_opts += ' ' + c_opt
        else:
            if not self.py_site_pkgs:
                site_packages_dir = self._guess_site_packages()
                if site_packages_dir:
                    self.log.debug('Making directory: %s' % site_packages_dir)
                    os.makedirs(site_packages_dir)
                    self.log.debug('Adding to PYTHONPATH: %s' % site_packages_dir)
                    self.env.update_env_var('pythonpath', site_packages_dir)
                install_opts = '--prefix=%s' % self.deploy_dir
            else:
                install_opts = '--install-scripts=%s' % self.deploy_dir
        rc = util.python_distutils(self.name,
                                   self.py_exe,
                                   setup_dir,
                                   self.py_build_opts,
                                   install_opts)
        if rc != 0:
            self.log.error('Problem building %s.' % self.name)
            return 1
        else:
            self.log.info('Successfully built %s.' % self.name)
        return 0

    def _deploy_make(self, setup_dir):
        rc = util.make(self.name, setup_dir, self.make_opts)
        if rc != 0:
            self.log.error('Problem making %s.' % self.name)
            return 1
        else:
            self.log.info('Successfully made %s.' % self.name)
        return self._copy_dir(setup_dir)

    def _deploy_make_install(self, setup_dir):
        rc = util.make_install(self.name, setup_dir, self.make_install_opts)
        if rc != 0:
            self.log.error('Problem running make-install %s.' % self.name)
            return 1
        else:
            self.log.info('Successfully made %s.' % self.name)
        return self._copy_dir(setup_dir)

    def _deploy_do_copy(self, setup_dir):
        return self._copy_dir(setup_dir)

    def _deploy_custom(self, setup_dir):
        return custom.custom_deploy(self, setup_dir)

    def _compile_c_file(self, setup_dir):
        src_file = os.path.join(setup_dir, self.release_file_name)
        rc = util.compile_c_file(self.name,
                                 setup_dir,
                                 src_file,
                                 self.exe_name,
                                 self.c_compile_opts)
        if rc != 0:
            self.log.error('Problem compiling %s.' % self.name)
            return 1
        else:
            self.log.info('Successfully compiled %s.' % self.name)
        return self._copy_dir(setup_dir)

    def _compile_cpp_file(self, setup_dir):
        src_file = os.path.join(setup_dir, self.release_file_name)
        rc = util.compile_cpp_file(self.name,
                                   setup_dir,
                                   src_file,
                                   self.exe_name,
                                   self.cpp_compile_opts)
        if rc != 0:
            self.log.error('Problem compiling %s.' % self.name)
            return 1
        else:
            self.log.info('Successfully compiled %s.' % self.name)
        return self._copy_dir(setup_dir)

    def _execute_post_bash_cmds(self):
        if not self.post_bash_cmds:
            self.log.debug('No post bash commands to execute.')
            return 0
        self.log.info('Executing post bash commands for %s' % self.name)
        os.chdir(self.deploy_dir)
        self.log.debug('EXE: %s' % self.post_bash_cmds)
        (bStatus, bOut) = commands.getstatusoutput(self.post_bash_cmds)
        if bStatus == 0:
            self.log.info('%s post bash commands succeeded' % self.name)
        else:
            self.log.error('%s post bash commands failed' % self.name)
            self.log.debug('bash commands failed, return code: ' + \
                         '%s' % bStatus)
            self.log.debug('Output: %s' % bOut)
            return 1
        return 0

    def _deploy_ant(self, setup_dir):
        rc = self._copy_dir(setup_dir)
        if rc == 0:
            rc = util.ant(self.name, self.deploy_dir)
        return rc

    def _update_env(self):
        for rel_path in self.rel_path_dirs:
            self.log.debug('Adding to PATH: %s' % rel_path)
            self.env.update_env_var('path', rel_path)
        for env_var in self.env_vars:
            self.log.debug('Adding to environment: %s' % env_var)
            env_var_name = env_var.split('=')[0]
            env_var_value = env_var.split('=')[1]
            self.env.update_env_var(env_var_name, env_var_value)
        if (self.build_type == 'python-distutils') and (not self.py_site_pkgs):
            site_packages_dir = self._guess_site_packages()
            self.log.debug('Adding to PYTHONPATH: %s' % site_packages_dir)
            self.env.update_env_var('pythonpath', site_packages_dir)

    def _delete_previous_repo_versions(self):
        base_name = self.name + '-' + \
                    self.version + '-' + \
                    self.deploy_type + '-'
        dirs = os.listdir(self.base_deploy_dir)
        remove_dirs = []
        for dirname in dirs:
            if base_name in dirname:
                if self.deploy_name not in dirname:
                    remove_dir = os.path.join(self.base_deploy_dir, dirname)
                    remove_dirs.append(remove_dir)
        for remove_dir in remove_dirs:
            removed_dir = util.remove_directory(remove_dir, True)

    def _terminate(self, rc=1):
        shutil.rmtree(self.tmp_dir)
        return rc
        
    def deploy(self):
        self.log.info('Deploying app: %s' % self.name)

        # create final deploy directory, or skip if exists
        if os.path.exists(self.deploy_dir):
            self.log.info('Deploy directory exists: %s' % self.deploy_dir)
            self.log.info('Skipping deployment, assuming successful.')
            self._update_env()
            return self._terminate(-1)
        else:
            self.log.info('Making deploy directory: %s' % self.deploy_dir)
            os.makedirs(self.deploy_dir)

        # download to tmp_dir
        if self._download() != 0:
            self.log.error('%s download failed.' % self.name)
            return self._terminate(1)

        # unzip, if needed, only applies to release deployments
        if self.deploy_type == 'release':
            file_path = os.path.join(self.tmp_dir, self.release_file_name)
            if util.unzip_file(file_path, self.tmp_dir) == 0:
                self.log.info('Unzip succeeded: %s' % file_path)
            else:
                self.log.error('Unzip failed: %s' % file_path)
                return self._terminate(1)

            if self.unzipped_name:
                self.log.debug('Using specified unzipped name: %s' % self.unzipped_name)
                setup_dir = os.path.join(self.tmp_dir, self.unzipped_name)
            else:
                self.log.debug('Using tmp directory name: %s' % self.tmp_dir)
                setup_dir = self.tmp_dir

            if not os.path.exists(setup_dir):
                self.log.error('Unzipped directory does not exist: %s' % setup_dir)
                return self._terminate(1)
            else:
                self.log.debug('The unzipped directory exists: %s' % setup_dir)
        else:
            setup_dir = os.path.join(self.tmp_dir, self.repository_local_name)

        # build
        rc = 0
        if self.build_type == 'autoconf':
            rc = self._deploy_autoconf(setup_dir)
        elif self.build_type == 'python-distutils':
            rc = self._deploy_python_distutils(setup_dir)
        elif self.build_type == 'make':
            rc = self._deploy_make(setup_dir)
        elif self.build_type == 'make-install':
            rc = self._deploy_make_install(setup_dir)
        elif self.build_type == 'c-file':
            rc = self._compile_c_file(setup_dir)
        elif self.build_type == 'cpp-file':
            rc = self._compile_cpp_file(setup_dir)
        elif self.build_type == 'custom':
            rc = self._deploy_custom(setup_dir)
        elif self.build_type == 'copy':
            rc = self._deploy_do_copy(setup_dir)
        elif self.build_type == 'ant':
            rc = self._deploy_ant(setup_dir)
        else:
            self.log.error('Unrecognized build type: %s' % self.build_type)
            return self._terminate(1)

        # actions to complete if the deploy was successful
        if rc == 0:
            if self.cp_src_dir:
                rc = util.recursive_copy_all_files(setup_dir, self.deploy_dir)
            if self.repo_version and self.remove_repos:
                self._delete_previous_repo_versions()
            self._update_env()
            rc = self._execute_post_bash_cmds()

        return self._terminate(rc)
