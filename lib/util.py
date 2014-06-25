from urllib import FancyURLopener

import commands
import logging
import os
import shutil
import sys

log = logging.getLogger(__name__)

def remove_directory(dir_path, force_remove=False):
    if force_remove:
        if os.path.exists(dir_path) and \
           (not is_protected_dir(dir_path)):
            logmsg = 'Removing directory: '
            logmsg += '%s' % dir_path
            log.info(logmsg)
            shutil.rmtree(dir_path)
        else:
            logmsg = 'Unable to remove directory: '
            logmsg += '%s' % dir_path
            log.error(logmsg)
    else:
        if os.path.exists(dir_path) and \
           (not is_protected_dir(dir_path)):
            try:
                logmsg = 'Removing directory: '
                logmsg += '%s' % dir_path
                log.info(logmsg)
                os.rmdir(dir_path)
            except:
                logmsg = 'Directory is not empty. '
                logmsg += 'It must be removed manually: %s' % dir_path
                log.error(logmsg)
                return dir_path
    return None

def is_protected_dir(dir_path):
    PROTECTED_DIRS = ['/', '', '/bin', '/boot', '/dev', '/etc', '/home', \
                      '/lib', '/mnt', '/opt', '/proc', '/root', '/sbin', \
                      '/sys', '/usr', '/var']
    if dir_path.strip() in PROTECTED_DIRS:
        return True
    return False

def get_git_repository_version(repoPath):
    if not repoPath:
        return

    version = None

    infoStr = 'git ls-remote %s refs/heads/master' % repoPath
    log.debug('EXE: %s' % infoStr)
    (infoStatus, infoOut) = commands.getstatusoutput(infoStr)
    if infoStatus == 0:
        if len(infoOut) > 1:
            commitid = infoOut.split()[0]
            if len(commitid) >= 8:
                version = commitid[-8:]
                log.debug('Got repository with %s commits' % (version))
        if not version:
            log.debug('Failed to get number of commits for %s' % repoPath)
            return
    else:
        log.debug('Failed to get number of commits for %s' % repoPath)
        log.debug('Output: %s' % infoOut)
        return

    return version


def get_svn_repository_version(repoPath):
    if not repoPath:
        return

    version = None

    infoStr = 'svn info %s | grep Revision' % repoPath
    log.debug('EXE: %s' % infoStr)
    (infoStatus, infoOut) = commands.getstatusoutput(infoStr)
    if infoStatus == 0:
        splitout = infoOut.split()
        if len(splitout) > 1:
            version = splitout[1].strip()
            log.debug('Got repository version %s' % (version))
        else:
            log.debug('Failed to get a repo version number for %s' % repoPath)
            return
    else:
        log.debug('Failed to get a repo version number for %s' % repoPath)
        log.debug('Output: %s' % infoOut)
        return

    return version

def line_in_file(line, filePath):
    filePath = os.path.expanduser(filePath)
    filePath = os.path.abspath(filePath)
    if os.path.exists(filePath):
        fileH = open(filePath, 'r')
        file_contents = fileH.readlines()
        fileH.close()
        if line in file_contents:
            return True
    return False

def backup_file(filePath):
    filePath = os.path.expanduser(filePath)
    filePath = os.path.abspath(filePath)
    fileDir = os.path.dirname(filePath)
    os.chdir(fileDir)
    if os.path.exists(filePath):
        newFileName = get_unique_filename(filePath)
        log.info('Backing up %s to %s' % (filePath, newFileName))
        shutil.copy2(filePath, newFileName)

def get_unique_filename(filePath):
    fileDirName = os.path.dirname(filePath)
    fileName = os.path.basename(filePath)
    newFileName = fileName + '.bak'
    count = 0

    checkFileName = newFileName
    fileExists = True
    while fileExists:
        filePath = os.path.join(fileDirName, checkFileName)
        if os.path.exists(filePath):
            checkFileName = newFileName + '.' + str(count)
            count += 1
        else:
            fileExists = False
    return filePath

def write_new_file(fileName, lines):
    filePath = os.path.expanduser(fileName)
    filePath = os.path.abspath(filePath)
    fileDir = os.path.dirname(filePath)
    log.debug('Writing new file: %s' % filePath)
    os.chdir(fileDir)
    newFile = open(filePath, 'w')
    for line in lines:
        newFile.write(line)
    newFile.close()

def make_file_user_executable(filePath):
    srcDir = os.path.dirname(filePath)
    os.chdir(srcDir)
    exeStr = 'chmod +x %s' % filePath
    log.debug('EXE: %s' % exeStr)
    (exeStatus, exeOut) = commands.getstatusoutput(exeStr)
    if exeStatus == 0:
        log.debug('File %s is now executable' % filePath)
    else:
        log.debug('Failed to make %s executable' % filePath)
        log.debug('Output: %s' % exeOut)
        return 1
    return 0

def move_file(srcFile, destFile):
    log.debug('Moving %s to %s' % (srcFile, destFile))
    try:
        shutil.move(srcFile, destFile)
    except:
        log.debug('Failed moving %s to %s' % (srcFile, destFile))
        return 1
    return 0

def recursive_copy_all_files(srcDir, destDir):
    cpStr = 'cp -r %s/* %s/' % (srcDir, destDir)
    log.debug('EXE: %s' % cpStr)
    (cpStatus, cpOut) = commands.getstatusoutput(cpStr)
    if cpStatus == 0:
        log.debug('Copy of %s to %s succeeded' % (srcDir, destDir))
    else:
        log.debug('Failed to copy %s to %s' % (srcDir, destDir))
        log.debug('Output: %s' % cpOut)
        return 1
    return 0

def copytree(srcDir, destDir):
    log.debug('Copying %s to %s' % (srcDir, destDir))
    try:
        shutil.copytree(srcDir, destDir)
    except shutil.Error, e:
        # Taken and modified from:
        # https://mail.python.org/pipermail/python-bugs-list/2010-April/097195.html
        for src, dst, error in e.args[0]:
            if not os.path.islink(src):
                return 1
            else:
                linkto = os.readlink(src)
                if os.path.exists(linkto):
                    return 1
                else:
                    # dangling symlink found.. ignoring..
                    pass
    except:
        return 1
    return 0

def git_clone(URL, destDir, localFileName, repoOpt):
    log.info('Cloning %s to %s' % (URL, destDir))
    os.chdir(destDir)
    log.debug('Join %s and %s' % (destDir, localFileName))
    downloadDir = os.path.join(destDir, localFileName)
    gitStr = 'git clone %s %s %s' % (repoOpt, URL, downloadDir)
    log.debug('EXE: %s' % gitStr)
    (gitStatus, gitOut) = commands.getstatusoutput(gitStr)
    if gitStatus == 0:
        log.debug('git clone succeeded: %s' % URL)
    else:
        log.error('git clone failed: %s' % URL)
        log.debug('Output: %s' % gitOut)
        return 1
    return 0

def svn_checkout(URL, destDir, localFileName, repoOpt):
    log.info('Checking out %s' % URL)
    os.chdir(destDir)
    downloadDir = os.path.join(destDir, localFileName)
    svnStr = 'svn co %s %s %s' % (repoOpt, URL, downloadDir)
    log.debug('EXE: %s' % svnStr)
    (svnStatus, svnOut) = commands.getstatusoutput(svnStr)
    if svnStatus == 0:
        log.debug('svn checkout succeeded: %s' % URL)
    else:
        log.error('svn checkout failed: %s' % URL)
        log.debug('Output: %s' % svnOut)
        return 1
    return 0

def ant(appName, baseDir):
    os.chdir(baseDir)
    buildStr = 'ant'
    log.debug('EXE: %s' % buildStr)
    (buildStatus, buildOut) = commands.getstatusoutput(buildStr)
    if buildStatus == 0:
        log.debug('%s build succeeded' % appName)
    else:
        log.error('Failed to build %s' % appName)
        log.debug('Build failed, return code: ' + \
                     '%s' % buildStatus)
        log.debug('Output: %s' % buildOut)
        return 1
    return 0

def python_distutils(appName,
                     pyExe,
                     setupDir,
                     buildOpts=None,
                     installOpts=None):
    if not buildOpts:
        buildOpts = ''
    if not installOpts:
        installOpts = ''
    log.info('Building %s' % appName)
    os.chdir(setupDir)
    buildStr = pyExe + ' setup.py build %s' % buildOpts
    log.debug('EXE: %s' % buildStr)
    (buildStatus, buildOut) = commands.getstatusoutput(buildStr)
    if buildStatus == 0:
        log.debug(appName + ' build succeeded')
    else:
        log.error('Failed to build ' + appName)
        log.debug(appName + ' build failed, return code: ' + \
                     '%s' % buildStatus)
        log.debug('Output: %s' % buildOut)
        return 1

    log.info('Installing %s' % appName)
    os.chdir(setupDir)
    installStr = pyExe + ' setup.py install %s' % installOpts
    log.debug('EXE: %s' % installStr)
    (installStatus, installOut) = commands.getstatusoutput(installStr)
    if installStatus == 0:
        log.debug(appName + ' install succeeded')
    else:
        log.error('Failed to install ' + appName)
        log.debug(appName + ' install failed, return code: ' + \
                     '%s' % installStatus)
        log.debug('Output: %s' % installOut)
        return 1
    return 0

def compile_cpp_file(appName, srcDir, srcFile, exeFile, extraOpt=None):
    if not extraOpt:
        extraOpt = ''
    log.info('Compiling %s' % appName)
    os.chdir(srcDir)
    compileStr = 'g++ ' + '-o ' + exeFile + ' ' + srcFile + ' ' + extraOpt
    log.debug('EXE: %s' % compileStr)
    (compileStatus, compileOut) = commands.getstatusoutput(compileStr)
    if compileStatus == 0:
        log.debug(appName + ' compile succeeded')
    else:
        log.error('Failed to compile ' + appName)
        log.debug(appName + ' compile failed, return code: ' + \
                     '%s' % compileStatus)
        log.debug('Output: %s' % compileOut)
        return 1
    return 0

def compile_c_file(appName, srcDir, srcFile, exeFile, extraOpt=None):
    if not extraOpt:
        extraOpt = ''
    log.info('Compiling %s' % appName)
    os.chdir(srcDir)
    compileStr = 'gcc ' + '-o ' + exeFile + ' ' + srcFile + ' ' + extraOpt
    log.debug('EXE: %s' % compileStr)
    (compileStatus, compileOut) = commands.getstatusoutput(compileStr)
    if compileStatus == 0:
        log.debug(appName + ' compile succeeded')
    else:
        log.error('Failed to compile ' + appName)
        log.debug(appName + ' compile failed, return code: ' + \
                     '%s' % compileStatus)
        log.debug('Output: %s' % compileOut)
        return 1
    return 0

def make_install(appName, srcDir, extraOpt=None):
    if not extraOpt:
        extraOpt = ''
    log.info('Compiling %s' % appName)
    os.chdir(srcDir)
    compileStr = 'make ' + extraOpt
    log.debug('EXE: %s' % compileStr)
    (compileStatus, compileOut) = commands.getstatusoutput(compileStr)
    if compileStatus == 0:
        log.debug(appName + ' make succeeded')
    else:
        log.error('Failed to compile ' + appName)
        log.debug(appName + ' make failed, return code: ' + \
                     '%s' % compileStatus)
        log.debug('Output: %s' % compileOut)
        return 1
    os.chdir(srcDir)
    installStr = 'make install'
    log.debug('EXE: %s' % installStr)
    (installStatus, installOut) = commands.getstatusoutput(installStr)
    if installStatus == 0:
        log.debug(appName + ' make install succeeded')
    else:
        log.error('Failed to install ' + appName)
        log.debug(appName + ' make install failed, return code: ' + \
                     '%s' % installStatus)
        log.debug('Output: %s' % installOut)
        return 1
    return 0

def make(appName, srcDir, extraOpt=None):
    if not extraOpt:
        extraOpt = ''
    log.info('Compiling %s' % appName)
    os.chdir(srcDir)
    compileStr = 'make ' + extraOpt
    log.debug('EXE: %s' % compileStr)
    (compileStatus, compileOut) = commands.getstatusoutput(compileStr)
    if compileStatus == 0:
        log.debug(appName + ' make succeeded')
    else:
        log.error('Failed to compile ' + appName)
        log.debug(appName + ' make failed, return code: ' + \
                     '%s' % compileStatus)
        log.debug('Output: %s' % compileOut)
        return 1
    return 0

def gnu_autoconf(appName, setupDir, deployDir, customConf=None, customMake=None, customMakeInstall=None):
    if not customConf:
        customConf = ''
    if not customMake:
        customMake = ''
    if not customMakeInstall:
        customMakeInstall = ''
    log.info('Configuring %s' % appName)
    os.chdir(setupDir)
    configureStr = setupDir + '/configure --prefix=' + \
                   '%s %s' % (deployDir, customConf)
    log.debug('EXE: %s' % configureStr)
    (confStatus, confOut) = commands.getstatusoutput(configureStr)
    if confStatus == 0:
        log.debug(appName + ' configure succeeded')
    else:
        log.error('Failed to configure ' + appName)
        log.debug(appName + ' configure failed, return code: ' + \
                     '%s' % confStatus)
        log.debug('Output: %s' % confOut)
        return 1

    log.info('Compiling %s' % appName)
    os.chdir(setupDir)
    makeStr = 'make %s' % customMake
    log.debug('EXE: %s' % makeStr)
    (makeStatus, makeOut) = commands.getstatusoutput(makeStr)
    if makeStatus == 0:
        log.debug(appName + ' make succeeded')
    else:
        log.error('Failed to compile ' + appName)
        log.debug(appName + ' make failed, return code: ' + \
                     '%s' % makeStatus)
        log.debug('Output: %s' % makeOut)
        return 1

    log.info('Installing %s' % appName)
    os.chdir(setupDir)
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

def unzip_file(filePath, newLocation):
    fileDir = os.path.dirname(filePath)
    os.chdir(fileDir)
    if filePath.endswith('.zip'):
        unzipApp = 'unzip %s -d %s'
    elif filePath.endswith('.bz2'):
        unzipApp = 'tar -jxf %s -C %s'
    elif ((filePath.endswith('.tar.gz')) or (filePath.endswith('.tgz'))):
        unzipApp = 'tar -zxf %s -C %s'
    else:
        log.debug('The file does not appear to be zipped: %s' % filePath)
        log.debug('Skipping unzip: %s' % filePath)
        return 0
    unzipApp = unzipApp % (filePath, newLocation)
    log.debug('Unzipping %s' % filePath)
    log.debug('EXE: %s' % unzipApp)
    (unzipStatus, unzipOut) = commands.getstatusoutput(unzipApp)
    if unzipStatus == 0:
        log.debug('Unzip succeeded')
    else:
        log.debug('Unzip failed, return code %s' % unzipStatus)
        log.debug('Output: %s' % unzipOut)
        return 1
    return 0

def progress_reporter(s):
    log.debug(s)

class URLOpener(FancyURLopener):
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        msg = 'ERROR: Could not download %s\nIs the URL valid?' % url
        raise IOError, msg

def download_file(URL, dest_dir, local_file, num_retries = 4):
    log.info('Downloading %s' % URL)
    url_opener = URLOpener()
    localFP = os.path.join(dest_dir, local_file)
    tmpDownloadFP = '%s.part' % localFP
    progress_reporter('Starting %s download' % local_file)
    progress_reporter('%s ==> %s' % (URL, localFP))

    download_failed = num_retries
    rc = 1
    while download_failed > 0:
        try:
            tmpLocalFP, headers = url_opener.retrieve(URL, \
                                                      tmpDownloadFP)
            os.rename(tmpDownloadFP, localFP)
            rc = 0
        except IOError, msg:
            if download_failed == 1:
                progress_reporter('Download of %s failed.' % URL)
            else:
                progress_reporter('Download failed. Trying again...' + \
                                  '%s tries remain.' % str(download_failed-1))
            download_failed -= 1
        else:
            download_failed = 0
            progress_reporter('%s downloaded successfully.' % local_file)
    return rc
