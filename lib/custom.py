from lib import util

import commands
import os
import stat
import logging

log = logging.getLogger(__name__)

"""
If additional applications are added to the config file with the build-type
of "custom" this file must be modified. Modifications include:
  1. Add a function to deploy the application correctly. This function should
     return 0 if successful and non-zero if unsuccessful.
  2. Add the appropriate lines to the "custom_deploy" function to call the
     new custom function.

The app.name in custom_deploy matches the [name] of the application specified
in the config file. Additionally, other supported options (see README) can be
accessed via the app object that is passed into custom_deploy (see
application.py).
"""
def update_denoiser_settings(deployDir):
    settings_file = deployDir + '/Denoiser/settings.py'
    f = open(settings_file, 'r')
    lines = f.readlines()
    f.close()
    new_lines = []
    for line in lines:
        split_line = line.split()
        if len(split_line) >  2:
            if (split_line[0] == 'PROJECT_HOME') and \
               (split_line[1] == '='):
                new_line = 'PROJECT_HOME     = ' + \
                           '\"%s/\"\n' % deployDir
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    f = open(settings_file, 'w')
    for line in new_lines:
        f.write(line)
    f.close()

def deploy_denoiser(app, setup_dir):
    os.rmdir(app.deploy_dir)
    util.copytree(setup_dir, app.deploy_dir)

    srcName = 'FlowgramAli_4frame_linux_x86_64'
    srcPath = os.path.join(app.deploy_dir, 'FlowgramAlignment')
    srcPath = os.path.join(srcPath, srcName)

    destName = 'FlowgramAli_4frame'
    destPath = os.path.join(app.deploy_dir, 'bin')
    destPath = os.path.join(destPath, destName)

    rc = util.move_file(srcPath, destPath)
    if rc != 0:
        return rc

    update_denoiser_settings(app.deploy_dir)

    baseDir = os.path.join(app.deploy_dir, 'Denoiser')
    files = ['denoiser.py', 'preprocess.py', 'denoise_postprocess.py', \
             'make_cluster_jobs.py']
    for aFile in files:
        filePath = os.path.join(baseDir, aFile)
        rc = util.make_file_user_executable(filePath)
        if rc != 0:
            app.log.error('Problem making %s executable.' % filePath)
    
    return 0

def deploy_uclust(app, setup_dir):
    old_path = os.path.join(app.tmp_dir, app.release_file_name)
    new_path = os.path.join(app.deploy_dir, 'uclust')
    rc = util.move_file(old_path, new_path)
    if rc == 0:
        rc = util.make_file_user_executable(new_path)
        if rc == 0:
            return 0
    return 1

def deploy_pyronoise(app, setup_dir):
    srcDir = os.path.join(setup_dir, 'FDist')
    rc = util.make('pyronoise2/FDist', srcDir)
    if rc != 0:
        return rc
    srcDir = os.path.join(setup_dir, 'FastaUnique')
    rc = util.make('pyronoise2/FastaUnique', srcDir)
    if rc != 0:
        return rc
    srcDir = os.path.join(setup_dir, 'NDist')
    rc = util.make('pyronoise2/NDist', srcDir)
    if rc != 0:
        return rc
    srcDir = os.path.join(setup_dir, 'PCluster')
    rc = util.make('pyronoise2/PCluster', srcDir)
    if rc != 0:
        return rc
    srcDir = os.path.join(setup_dir, 'QCluster')
    rc = util.make('pyronoise2/QCluster', srcDir)
    if rc != 0:
        return rc

    os.rmdir(app.deploy_dir)
    return util.copytree(setup_dir, app.deploy_dir)

def deploy_ampliconnoise(app, setup_dir):
    rc = util.make_install('ampliconnoise', setup_dir)
    if rc != 0:
        return rc

    # Certain versions of AmpliconNoise have a bad symlink that needs to be
    # removed, while other versions do not. We use a try/except structure
    # instead of using os.path.exists() because broken symlinks will return
    # False.
    filePath = os.path.join(setup_dir, 'PyroNoiseM/.#Head10.dat')
    try:
        os.remove(filePath)
    except OSError:
        pass

    os.rmdir(app.deploy_dir)
    return util.copytree(setup_dir, app.deploy_dir)

def deploy_sortmerna(app, setup_dir):
    """Deploy SortMeRNA by calling package-distributed build.sh
       which will execute configure, touch command and make.
       The touch command is (order-specific):
        touch configure.ac aclocal.m4 configure \
            Makefile.am Makefile.in
       to overcome the timestamp issues associated
       with cloning software which use autoconf.
    """
    customConf = app.ac_config_opts
    if not customConf:
        customConf = ''
    customMakeInstall = app.ac_make_install_opts
    if not customMakeInstall:
        customMakeInstall = ''
    deployDir = app.deploy_dir
    appName = app.name

    # run build.sh (contains configure, touch commands and make)
    os.chdir(setup_dir)
    log.info('Building %s' % appName)
    buildStr = setup_dir + '/build.sh --prefix=' + \
                   '%s %s' % (deployDir, customConf)
    log.debug('EXE: %s' % buildStr)
    (confStatus, confOut) = commands.getstatusoutput(buildStr)
    if confStatus == 0:
        log.debug(appName + ' build succeeded')
    else:
        log.error('Failed to build ' + appName)
        log.debug(appName + ' build failed, return code: ' + \
                     '%s' % confStatus)
        log.debug('Output: %s' % confOut)
        return 1

    # run make install
    log.info('Installing %s' % appName)
    os.chdir(setup_dir)
    makeiStr = 'make install %s' % customMakeInstall
    log.debug('EXE: %s' % makeiStr)
    (makeiStatus, makeiOut) = commands.getstatusoutput(makeiStr)
    if makeiStatus == 0:
        log.debug(appName + ' make install succeeded')
    else:
        log.error('Failed to install ' + appName)
        log.debug(appName + ' make install failed, return code: ' + \
                     '%s' % makeiStatus)
        log.debug('Output: %s' % makeiOut)
        return 1
    return 0

def deploy_vienna(app, setup_dir):
    # a hack to add a header file
    srcFile = os.path.join(setup_dir, 'RNAforester/src/rnafuncs.cpp')
    fileH = open(srcFile, 'r')
    fileC = fileH.readlines()
    fileH.close()
    fileH = open(srcFile, 'w')
    fileH.write('#include <stdio.h>')
    for line in fileC:
        fileH.write(line)
    fileH.close()

    return app._deploy_autoconf(setup_dir)
    
def deploy_pysparse(app, setup_dir):
    # a hack to add a header file    
    setupFile = os.path.join(setup_dir, 'setup.py')
    fileH = open(setupFile, 'r')
    fileC = fileH.readlines()
    fileH.close()
    fileH = open(setupFile, 'w')
    for line in fileC:
        line = str.replace(line, "'lapack', 'blas'", '')   
        fileH.write(line)
    fileH.close()

    return app._deploy_python_distutils(setup_dir)

def deploy_dotur(app, setup_dir):
    # a hack to fix headers for gcc 4.3+
    richFile = os.path.join(setup_dir, 'richness.h')
    fileH = open(richFile, 'r')
    fileC = fileH.readlines()
    fileH.close()
    fileH = open(richFile, 'w')
    fileH.write('#include <cstdlib>\n')
    for line in fileC:
        fileH.write(line)
    fileH.close()
    otuFile = os.path.join(setup_dir, 'otu.h')
    fileH = open(otuFile, 'r')
    fileC = fileH.readlines()
    fileH.close()
    fileH = open(otuFile, 'w')
    fileH.write('#include <cstdlib>\n#include <algorithm>\n')
    for line in fileC:
        fileH.write(line)
    fileH.close()
    doturFile = os.path.join(setup_dir, 'dotur.C')
    fileH = open(doturFile, 'r')
    fileC = fileH.readlines()
    fileH.close()
    fileH = open(doturFile, 'w')
    fileH.write('#include <cstring>\n')
    for line in fileC:
        fileH.write(line)
    fileH.close()

    srcFile = 'dotur.C'
    srcFile = os.path.join(setup_dir, srcFile)

    if app.exe_name:
        exeFile = app.exe_name
    else:
        exeFile = 'dotur'
    exeFile = os.path.join(setup_dir, exeFile)

    rc = util.compile_cpp_file('dotur', setup_dir, srcFile, exeFile)
    if rc != 0:
        return rc

    os.rmdir(app.deploy_dir)
    return util.copytree(setup_dir, app.deploy_dir)

def _generate_qiime_config(python_path, deploy_dir, all_apps_to_deploy, log,
                           qiime_config_path):
    qiime_path = None
    blast_path = None
    blast_data_path = None
    deploy_dir_contents = os.listdir(deploy_dir)
    for app in all_apps_to_deploy:
        if app.name == 'qiime':
            qiime_path = os.path.join(app.deploy_dir, 'bin')
        if app.name == 'blast':
            blast_path = os.path.join(app.deploy_dir, 'bin/blastall')
            blast_data_path = os.path.join(app.deploy_dir, 'data')

    log.info('Generating new %s file' % qiime_config_path)

    lines = []
    lines.append('# autogenerated by qiime-deploy\n')

    if qiime_path:
        # If we have a [qiime] target, write out additional QIIME config lines
        # for qiime_scripts_dir, etc.. These values have since been removed (or
        # replaced by defaults) in QIIME, but we'll continue to write them here
        # to maintain backwards compatibility with older qiime-deploy conf
        # files that still deploy QIIME instead of assuming that QIIME's python
        # code is already installed (e.g., via pip).
        line = 'qiime_scripts_dir\t%s\n' % qiime_path
        lines.append(line)

        line = 'python_exe_fp\t%s\n' % python_path
        lines.append(line)

        lines.append('working_dir\t/tmp/\n')
        lines.append('temp_dir\t/tmp/\n')

        # for n3phele
        lines.append('cloud_environment\tFalse\n')

        path = deploy_dir + '/lanemask_in_1s_and_0s'
        line = 'template_alignment_lanemask_fp\t%s\n' % path
        lines.append(line)

        path = deploy_dir + '/core_set_aligned.fasta.imputed'
        line = 'pynast_template_alignment_fp\t%s\n' % path
        lines.append(line)

        # lines for Greengenes files
        path = deploy_dir + '/gg_otus-13_8-release/rep_set/97_otus.fasta'
        line = 'assign_taxonomy_reference_seqs_fp\t%s\n' % path
        lines.append(line)

        path = deploy_dir + '/gg_otus-13_8-release/taxonomy/97_otu_taxonomy.txt'
        line = 'assign_taxonomy_id_to_taxonomy_fp\t%s\n' % path
        lines.append(line)

        parallel_jobs_path = os.path.join(qiime_path, 'start_parallel_jobs.py')
        lines.append('cluster_jobs_fp\t%s\n' % parallel_jobs_path)

    # The following QIIME config values are set regardless of whether we're
    # deploying the latest QIIME or previous versions.
    if blast_path:
        line = 'blastall_fp\t%s\n' % blast_path
        lines.append(line)

    if blast_data_path:
        line = 'blastmat_dir\t%s\n' % blast_data_path
        lines.append(line)

    lines.append('')
    lines.append('')

    old_contents = []
    if os.path.exists(qiime_config_path):
        oldFile = open(qiime_config_path, 'r')
        old_contents = oldFile.readlines()
        oldFile.close()

    if lines != old_contents:
        util.backup_file(qiime_config_path)
        if os.path.exists(qiime_config_path):
            os.remove(qiime_config_path)

        util.write_new_file(qiime_config_path, lines)

        log.info('Generated new %s file' % qiime_config_path)

    return 0

def custom_deploy(app, setup_dir):
    app.log.debug('Deploying custom application: %s' % app.name)
    if app.name == 'denoiser':
        return deploy_denoiser(app, setup_dir)
    elif app.name == 'uclust':
        return deploy_uclust(app, setup_dir)
    elif app.name == 'pyronoise':
        return deploy_pyronoise(app, setup_dir)
    elif app.name == 'ampliconnoise':
        return deploy_ampliconnoise(app, setup_dir)
    elif app.name == 'dotur':
        return deploy_dotur(app, setup_dir)
    elif app.name == 'vienna':
        return deploy_vienna(app, setup_dir)
    elif app.name == 'pysparse':
        return deploy_pysparse(app, setup_dir)
    elif app.name == 'sortmerna':
        return deploy_sortmerna(app, setup_dir)
    app.log.error('Unrecognized application: %s' % app.name)
    return 1

def set_permissions_all_files(deploy_dir):
    for dir_path, dir_names, file_names in os.walk(deploy_dir):
        for f in file_names:
            full_name = os.path.join(dir_path, f)
            st = os.stat(full_name)
            # if the user can execute it, set 755
            if bool(st.st_mode & stat.S_IEXEC):
                os.chmod(full_name, int("755", 8))
            # if the user can't execute it, set it to 644
            else:
                os.chmod(full_name, int("644", 8))
        # set directories to 755
        for d in dir_names:
            full_path = os.path.join(dir_path, d)
            os.chmod(full_path, int("755", 8))

"""
Any custom finalization code (after deploy is complete) should go here. In
QIIME's case, we'll generate the qiime_config file.
"""
def custom_finalize(python_path, deploy_dir, all_apps_to_deploy, log,
                    qiime_config_path):
    set_permissions_all_files(deploy_dir)
    return _generate_qiime_config(python_path, deploy_dir, all_apps_to_deploy,
                                  log, qiime_config_path)
