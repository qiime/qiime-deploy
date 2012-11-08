from lib import application
from lib import config
from lib import custom
from lib import data
from lib import dependencies
from lib import deploy
from lib import environment
from lib import logconfig
from lib import util
from optparse import OptionParser

import commands
import logging
import os
import shutil
import sys
import time

SLEEP_SECS = 5

def generate_activate_file(print_env, 
                           deploy_dir, 
                           append_to_bashrc=False,
                           append_to_bashprofile=False):
    log.info('Generating activate.sh file')

    lines = []
    for env_name in print_env:
        old_var = print_env[env_name]
        if (env_name.upper() == 'PATH') or \
           (env_name.upper() == 'PYTHONPATH'):
            new_var = old_var + ':$%s' % env_name.upper()
        else:
            new_var = old_var
        var_string = 'export %s=%s' % (env_name, new_var)
        var_string += '\n'
        lines.append(var_string)

    output_file = os.path.join(deploy_dir, 'activate.sh')

    old_contents = []
    if os.path.exists(output_file):
        oldFile = open(output_file, 'r')
        old_contents = oldFile.readlines()
        oldFile.close()

    if lines != old_contents:
        util.backup_file(output_file)
        if os.path.exists(output_file):
            os.remove(output_file)

        util.write_new_file(output_file, lines)

    appendStr = 'echo "source %s" >> ~/.bashrc' % output_file
    appendFile = '~/.bashrc'
    compStr = 'source %s\n' % output_file
    if (append_to_bashrc) and (not util.line_in_file(compStr, appendFile)):
        log.debug('Appending environment settings to ~/.bashrc')
        (appendStatus, appendOut) = commands.getstatusoutput(appendStr)
        if appendStatus != 0:
            log.error('Error appending to ~/.bashrc')
            log.error('Output:')
            log.error(appendOut)
        else:
            log.info('Successfully appended to ~/.bashrc')

    appendStr = 'echo "source %s" >> ~/.bash_profile' % output_file
    appendFile = '~/.bash_profile'
    compStr = 'source %s\n' % output_file
    if (append_to_bashprofile) and (not util.line_in_file(compStr, appendFile)):
        log.debug('Appending environment settings to ~/.bash_profile')
        (appendStatus, appendOut) = commands.getstatusoutput(appendStr)
        if appendStatus != 0:
            log.error('Error appending to ~/.bash_profile')
            log.error('Output:')
            log.error(appendOut)
        else:
            log.info('Successfully appended to ~/.bash_profile')

def is_app_successful(app_name, app_list):
    for app in app_list:
        if app.name == app_name:
            if app.success:
                return True
    return False

def is_app_complete(app_name, app_list):
    for app in app_list:
        if app.name == app_name:
            if app.complete:
                return True
    return False

"""
This is the main thread responsible for deploying all applications and data
specified in the config file in the appropriate order and making sure
everything completes.
"""
def deploy_apps(deploy_config, force_remove=False, remove_repos=False):
    env = environment.BashEnvironment()

    # launch status thread
    threads = []
    log.info('Starting status thread.')
    t = deploy.StatusThread()
    t.start()
    threads.append(t)

    # launch worker threads
    try:
        num_threads = int(deploy_config.get('global', 'max-deploy-threads'))
    except:
        log.debug('Missing max-deploy-threads section. Setting to 1.')
        num_threads = 1
    log.info('Starting %s deploy threads.' % num_threads)
    for i in range(num_threads):
        t = deploy.WorkerThread()
        t.start()
        threads.append(t)

    # create final deploy directory location if it doesn't exist
    deploy_dir = deploy_config.get('global', 'final-deploy-directory')
    deploy_dir = os.path.expanduser(deploy_dir)
    deploy_dir = os.path.abspath(deploy_dir)

    if os.path.exists(deploy_dir):
        log.debug('Final deploy directory already exists: %s' % deploy_dir)
    else:
        log.debug('Creating final deploy directory: %s' % deploy_dir)
        os.makedirs(deploy_dir)

    # identify data and application sections in the config file
    all_sect = deploy_config.sections()
    req_sect = ['dependencies', 'global']
    data_sect = [x for x in all_sect if 'data-' in x]
    app_sect = list(set(all_sect) - (set(req_sect) | set(data_sect)))

    log.debug('All config sections: %s' % all_sect)
    log.debug('Required config sections: %s' % req_sect)
    log.debug('Data config sections: %s' % data_sect)
    log.debug('Application config sections: %s' % app_sect)

    log.info('Running deploy for data and apps without dependencies.')

    # locate the python exe that we should use for the deploy process (if
    # required)
    log.info('Searching for python...')
    custom_py_exe = None
    try:
        custom_py_exe = deploy_config.get('global', 'python-exe')
        if custom_py_exe == 'None':
            custom_py_exe = None
        else:
            custom_py_exe = os.path.expanduser(custom_py_exe)
            log.info('python-exe specified, using: %s' % custom_py_exe)
    except:
        log.info('python-exe is not specified.')
        custom_py_exe = None
    if not custom_py_exe:
        if 'python' in app_sect:
            log.info('Looks like python is being deployed, using that version')
            base_dir = deploy_config.get('global', 'final-deploy-directory')
            python_version = deploy_config.get('python', 'version')
            try:
                release_location = deploy_config.get('python', 'release-location')
                deploy_type = 'release'
            except:
                log.debug('%s has no release-location' % 'python')
                deploy_type = 'repository'
            python_dir = 'python-' + python_version + '-' + deploy_type
            custom_py_exe = os.path.join(base_dir, python_dir)
            custom_py_exe = os.path.join(custom_py_exe, 'bin/python')
            log.info('Setting python: %s' % custom_py_exe)
        else:
            log.info('Could not find a python, setting \'python\'')
            custom_py_exe = 'python'

    # create application objects for all apps to deploy
    all_apps_to_deploy = []
    remaining_apps_to_deploy = []
    for app_name in app_sect:
        a = application.Application(app_name,
                                    env,
                                    deploy_config,
                                    custom_py_exe,
                                    remove_repos)
        remaining_apps_to_deploy.append(a)
        all_apps_to_deploy.append(a)

    # create and schedule all data objects
    for data_name in data_sect:
        d = data.Data(data_name, env, deploy_config)
        deploy.WORK_Q.put(d)

    # immediately schedule all applications that do not contain dependencies
    for app in list(remaining_apps_to_deploy):
        if not app.deps:
            log.debug('Putting %s in the queue to deploy.' % app.name)
            deploy.WORK_Q.put(app)
            remaining_apps_to_deploy.remove(app)

    remaining_names = [app.name for app in remaining_apps_to_deploy]
    log.info('Launched initial deploy, remaining apps: %s' % remaining_names)

    # schedule applications with dependencies once all of an applications 
    # dependencies have completed successfully
    log.info('Deploying remaining apps.')
    while remaining_apps_to_deploy:
        for app in list(remaining_apps_to_deploy):
            all_deps_complete = True
            all_deps_successful = True
            for dep in app.deps:
                if not is_app_complete(dep, all_apps_to_deploy):
                    log.debug('%s dependencies remaining:%s' % (app.name, app.deps))
                    all_deps_complete = False
                if not is_app_successful(dep, all_apps_to_deploy):
                    log.debug('%s dependencies not yet successful:%s' % (app.name, app.deps))
                    all_deps_successful = False
                if dep not in app_sect:
                    log.error('Application will never complete, dependency' + \
                              'does not exist: %s' % dep)
                    app.success = False
                    app.complete = True
                    deploy.FAILED_Q.put(app)
                    remaining_apps_to_deploy.remove(app)
            if not app.complete:
                if all_deps_complete and all_deps_successful:
                    log.debug('Putting %s in the queue to deploy.' % app.name)
                    deploy.WORK_Q.put(app)
                    remaining_apps_to_deploy.remove(app)
                if all_deps_complete and (not all_deps_successful):
                    app.success = False
                    app.complete = True
                    log.error('Dependencies failed for %s.' % app.name)
                    deploy.FAILED_Q.put(app)
                    remaining_apps_to_deploy.remove(app)
        remaining_names = [app.name for app in remaining_apps_to_deploy]
        log.debug('Applications waiting on dependencies: %s' % remaining_names)
        log.debug('Control thread sleeping: %s seconds' % SLEEP_SECS)
        time.sleep(SLEEP_SECS)

    # wait for everything to complete
    deploy.WORK_Q.join()
    deploy.DONE = True
    for t in threads:
        t.join()

    summary = '\n\n'
    summary += 'DEPLOYMENT SUMMARY\n\n'
    # print out successful deployments
    first = True
    summary += 'Packages deployed successfully:\n'
    while not deploy.COMPLETE_Q.empty():
        item = deploy.COMPLETE_Q.get(False)
        if item:
            if not first:
                summary += ', %s' % item.name
            else:
                summary += '%s' % item.name
                first = False
    summary += '\n'

    # print out skipped deployments
    first = True
    summary += '\nPackages skipped (assumed successful):\n'
    while not deploy.SKIPPED_Q.empty():
        item = deploy.SKIPPED_Q.get(False)
        if item:
            if not first:
                summary += ', %s' % item.name
            else:
                summary += '%s' % item.name
                first = False
    summary += '\n'

    # print out failed applications at the end and perform cleanup
    failed_items = False
    first = True
    failed_list = []
    summary += '\nPackages failed to deploy:\n'
    while not deploy.FAILED_Q.empty():
        item = deploy.FAILED_Q.get(False)
        if item:
            failed_dir = util.remove_directory(item.deploy_dir, force_remove)
            if failed_dir:
                failed_list.append(failed_dir)
            if not first:
                summary += ', %s' % item.name
            else:
                summary += '%s' % item.name
                first = False
            failed_items = True
    summary += '\n\n'

    if failed_list:
        summary += 'Directories of failed applications must be removed ' + \
                   'manually or --force-remove-failed-dirs must be specified:'
        summary += '\n'
        for failed_dir in failed_list:
            summary += failed_dir
            summary += '\n'
    summary += '\n'

    # build and write out activate.sh
    log.debug('Writing new environment variables to activate.sh')
    log.debug('Print environment: %s' % env.get_print_env())
    try:
        append_bashrc = deploy_config.get('global', 'append-environment-to-bashrc')
        if append_bashrc == 'yes':
            append_bashrc = True
        else:
            append_bashrc = False
    except:
        log.debug('Did not find append-environment-to-bashrc option, skipping.')
        append_bashrc = False
    try:
        append_bashprofile = deploy_config.get('global', 'append-environment-to-bashprofile')
        if append_bashprofile == 'yes':
            append_bashprofile = True
        else:
            append_bashprofile = False
    except:
        log.debug('Did not find append-environment-to-bashprofile option, skipping.')
        append_bashprofile = False

    generate_activate_file(env.get_print_env(), 
                           deploy_dir, 
                           append_bashrc,
                           append_bashprofile)

    # run any custom finalization code, in QIIME's case, this is where
    # the QIIME config file is generated and written
    rc = custom.custom_finalize(custom_py_exe, deploy_dir, all_apps_to_deploy, log)

    sys.stdout.write(summary)
    if failed_items:
        rc = 1
    return rc

def get_options():
    usage = "usage: %prog [options] [deploy_path]"
    parser = OptionParser(usage=usage)

    parser.add_option('-f', '--config-file', action = 'store', \
                      dest = 'configFile', help = 'Custom location for ' + \
                      'app-deploy configuration file ' + \
                      '[default: %default]')

    parser.add_option('--force-remove-failed-dirs', action = 'store_true', \
                      dest = 'forceRemove', help = 'Force remove ' + \
                      'directories of applications that failed  ' + \
                      'to deploy successfully ' + \
                      '[default: %default]')

    parser.add_option('--force-remove-previous-repos', action = 'store_true', \
                      dest = 'removePreviousRepos', help = 'Force remove ' + \
                      'directories of previous repository deployments ' + \
                      '(assuming a later version succeeded) ' + \
                      '[default: %default]')

    parser.set_defaults(configFile='./qiime.conf',
                        forceRemove=False,
                        removePreviousRepos=False)

    opts, args = parser.parse_args()

    if opts.configFile != None:
        opts.configFile = os.path.expanduser(opts.configFile)
        opts.configFile = os.path.abspath(opts.configFile)

    return opts, args

def main():
    opts, args = get_options()
    
    deploy_config = config.read_config(opts.configFile)
    if args:
        deploy_dir = args[0]
        deploy_config.set('global', 'final-deploy-directory', deploy_dir)

    try:
        if deploy_config.get('global', 'log-level') == 'DEBUG':
            logging.getLogger('').setLevel(logging.DEBUG)
    except:
        log.debug('Missing log-level option. Setting to INFO.')

    if not dependencies.dependencies_ok(deploy_config):
        log.error('Dependency check failed.')
        return 1
    else:
        log.info('Dependencies look good.')

    return deploy_apps(deploy_config,
                       opts.forceRemove, 
                       opts.removePreviousRepos)

if __name__ == '__main__':
    logconfig.configure_log()
    log = logging.getLogger(__name__)
    sys.exit(main())
