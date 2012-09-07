import commands
import logging

"""
not currently checking for these required packages:
e.g. debian packages: libgsl0-dev, openjdk-6-jdk, libxml2, libxslt1.1, 
                      libxslt1-dev, ant, subversion, build-essential,
                      zlib1g-dev, libpng12-dev, libfreetype6-dev
                      mpich2, libreadline-dev, gfortran, unzip,
                      libmysqlclient16, libmysqlclient16-dev
"""
def dependencies_ok(config):
    log = logging.getLogger(__name__)

    sects = config.sections()
    if 'global' not in sects:
        log.error('No global section found in config file.')
        return False
    if 'dependencies' not in sects:
        log.error('No dependencies section found in config file.')
        return False

    try:
        cmds_list = config.get('dependencies', 'commands')
        cmds_list = cmds_list.split(',')
        cmds = [cmd.strip() for cmd in cmds_list]
    except:
        log.debug('No commands to check for.')
        cmds = []

    try:
        extra_bash_test = config.get('dependencies', 'extra-bash-test')
    except:
        log.debug('No extra bash test.')
        extra_bash_test = None

    try:
        final_directory = config.get('global', 'final-deploy-directory')
    except:
        log.error('Missing required final-deploy-directory section.')
        return False

    for cmd in cmds:
        checkStr = 'which %s' % cmd
        (checkStatus, checkOut) = commands.getstatusoutput(checkStr)
        if checkStatus != 0:
            log.error('Problem locating ' + cmd)
            log.error('Please install it and make sure it is in your path')
            return False
        else:
            log.debug('Found command: %s' % cmd)

    if extra_bash_test:
        checkStr = extra_bash_test
        (checkStatus, checkOut) = commands.getstatusoutput(checkStr)
        if checkStatus != 0:
            log.error('Problem executing: %s' % extra_bash_test)
            return False
        else:
            log.debug('Extra bash test was successful: %s' % extra_bash_test)

    return True
