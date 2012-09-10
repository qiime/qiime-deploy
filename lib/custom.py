from lib import util

import commands
import os

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

def deploy_r(app, setup_dir):
    rc = app._deploy_autoconf(setup_dir)

    if rc != 0:
        return 1

    # hack for qiime requirements, but that's pretty much this whole file
    # packages an array of ['pkgname','repository'] 
    packages = [['randomForest','http://cran.r-project.org'],\
                ['optparse','http://cran.r-project.org'],\
                ['vegan','http://cran.r-project.org'],\
                ['ape','http://cran.r-project.org'],\
                ['MASS','http://cran.r-project.org'],\
                ['gtools','http://cran.r-project.org'],\
                ['klaR','http://cran.r-project.org']]
    for pkg in packages:
        r_exe = os.path.join(app.deploy_dir, 'bin/R')
        makeStr  = "echo \"install.packages('%s',repos='%s')\" | %s --slave --vanilla" % (pkg[0],pkg[1],r_exe)
        (makeStatus, makeOut) = commands.getstatusoutput(makeStr)
        if makeStatus == 0:
            app.log.debug('deploy r %s packages install succeeded' % pkg[0]) 
        else:
            app.log.error('Failed to install %s r package from %s' % (pkg[0],pkg[1]))
            app.log.debug('r packages failed, return code: ' + \
                     '%s' % makeStatus)
            app.log.debug('Output: %s' % makeOut)
            return 1
            
    return 0

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

    # a bad symlink
    filePath = os.path.join(setup_dir, 'PyroNoiseM/.#Head10.dat')
    os.remove(filePath)

    os.rmdir(app.deploy_dir)
    return util.copytree(setup_dir, app.deploy_dir)

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

def _generate_qiime_config(python_path, deploy_dir, all_apps_to_deploy, log):
    log.info('Generating new ~/.qiime_config_default file')

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
      
    if not (qiime_path and \
            blast_path and \
            blast_data_path):
        log.error('Missing necessary path for ~/.qiime_config_default file.')
        log.error('Skipping generation of ~/.qiime_config_default')
        return 1

    lines = []
    lines.append('# autogenerated by qiime-deploy\n')

    parallel_jobs_path = os.path.join(qiime_path, 'start_parallel_jobs.py')
    lines.append('cluster_jobs_fp\t%s\n' % parallel_jobs_path)
    
    line = 'python_exe_fp\t%s\n' % python_path
    lines.append(line)

    line = 'qiime_scripts_dir\t%s\n' % qiime_path
    lines.append(line)

    line = 'blastmat_dir\t%s\n' % blast_data_path
    lines.append(line)
    line = 'blastall_fp\t%s\n' % blast_path
    lines.append(line)

    path = deploy_dir + '/lanemask_in_1s_and_0s'
    line = 'template_alignment_lanemask_fp\t%s\n' % path
    lines.append(line)

    path = deploy_dir + '/core_set_aligned.fasta.imputed'
    line = 'pynast_template_alignment_fp\t%s\n' % path
    lines.append(line)

    #line = 'pyronoise_data_fp\t%s' % denoiser_path
    #lines.append(line)

    lines.append('pynast_template_alignment_blastdb\t\n')

    lines.append('working_dir\t/tmp/\n')
    lines.append('jobs_to_start\t1\n')
    lines.append('seconds_to_sleep\t60\n')
    lines.append('temp_dir\t/tmp/\n')
    
    # lines for n3phele
    lines.append('cloud_environment\tFalse\n')
    
    #lines for Greengenes files
    path = deploy_dir + '/gg_otus-4feb2011-release/rep_set/gg_97_otus_4feb2011.fasta'
    line = 'assign_taxonomy_reference_seqs_fp\t%s\n' % path
    lines.append(line)
    path = deploy_dir + '/gg_otus-4feb2011-release/taxonomies/greengenes_tax_rdp_train.txt'
    line = 'assign_taxonomy_id_to_taxonomy_fp\t%s\n' % path
    lines.append(line)
    
    lines.append('')
    lines.append('')
    qiimeFileName = os.path.expanduser('~/.qiime_config_default')

    old_contents = []
    if os.path.exists(qiimeFileName):
        oldFile = open(qiimeFileName, 'r')
        old_contents = oldFile.readlines()
        oldFile.close()

    if lines != old_contents:
        util.backup_file(qiimeFileName)
        if os.path.exists(qiimeFileName):
            os.remove(qiimeFileName)

        util.write_new_file(qiimeFileName, lines)

        log.info('Generated new ~/.qiime_config_default file')

    return 0

def custom_deploy(app, setup_dir):
    app.log.debug('Deploying custom application: %s' % app.name)
    if app.name == 'denoiser':
        return deploy_denoiser(app, setup_dir)
    elif app.name == 'uclust':
        return deploy_uclust(app, setup_dir)
    elif app.name == 'r':
        return deploy_r(app, setup_dir)
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
    app.log.error('Unrecognized application: %s' % app.name)
    return 1

"""
Any custom finalization code (after deploy is complete) should go here. In
QIIME's case, we'll generate the qiime_config file.
"""
def custom_finalize(python_path, deploy_dir, all_apps_to_deploy, log):
    return _generate_qiime_config(python_path, deploy_dir, all_apps_to_deploy, log)
