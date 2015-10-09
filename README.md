# qiime-deploy

_qiime-deploy_ is a tool for building, configuring, and deploying many of
QIIME's dependencies on Linux systems.

**Note:** _qiime-deploy_ *does not* install every dependency necessary for a
complete QIIME installation. Python, R, and their respective requisite packages
are not installed because we expect users to install these dependencies using
standard package managers that are available for the language (e.g., using
```pip``` to install Python packages). Also, certain dependencies
(e.g., _usearch_) are not installed due to licensing restrictions.

## Getting started

To run _qiime-deploy_, you will first need to grab a configuration file. The
configuration file will tell _qiime-deploy_ what packages it should install.
You can find many QIIME deployment configuration files in the
_qiime-deploy-conf_ project [here](https://github.com/qiime/qiime-deploy-conf)
as well as a description of all possible options and the configuration file
format. There are also various other configuration files included for
installing QIIME-related projects/tools.

Also, while _qiime-deploy_ downloads, builds, and installs many of QIIME's
dependencies, it does expect common packages to already be installed on your
system. See below for a list of these prerequisites, which will differ depending
on your Linux distribution.

After the deploy completes it will generate an ```activate.sh``` file in the
base deploy directory. It is necessary to ```source``` that file in order to
set the environment created by _qiime-deploy_. For example, if the deploy
directory is ```/opt/qiime/``` you will need to run the following command:

    source /opt/qiime/activate.sh

__Note:__ By default, _qiime-deploy_ will append the above line to your
```~/.bashrc```. This is done so that you do not need to run the command
each time you open a new terminal. To disable this behavior, you will need to
modify the _qiime-deploy_ conf file (see the _qiime-deploy-conf_ project
[here](https://github.com/qiime/qiime-deploy-conf) for a description of the
options you can tweak).

### Setting up qiime-deploy on Ubuntu

While _qiime-deploy_ may work on various Linux distributions, it has been most
heavily tested on Ubuntu 11.10 and 12.04 LTS (64-bit) systems. Thus,
we provide a short guide to setting up your Ubuntu system so that it can run
_qiime-deploy_.

In order to ensure that you have the required prerequisite packages installed
on your Ubuntu system, perform the following steps. These steps require admin
(sudo) access. If you do not have sudo access, you must ask your system
administrator to grant you sudo access, or to run the following steps for you.

1. Open ```/etc/apt/sources.list``` with a text editor. You can use your
favorite text editor but we suggest _pico_ for simplicity. Note that at the
bottom of the screen you will have the commands to save, exit, etc.:

        sudo pico /etc/apt/sources.list

    Uncomment the universe and multiverse repositories in this file.

    Add the following line to the bottom of this file in order to install a
    newer version of R than is available by default on the system.

    For Ubuntu 11.10:

        deb http://cran.rstudio.com/bin/linux/ubuntu oneiric/

    For Ubuntu 12.04:

        deb http://cran.rstudio.com/bin/linux/ubuntu precise/
        
    For Ubuntu 14.04:

        deb http://cran.rstudio.com/bin/linux/ubuntu trusty/    

    Save and close this file.

2. Update your system to retrieve the latest list of packages (this step is
especially important because we added new package repositories in the previous
step):

        sudo apt-get -y update

3. Install the _qiime-deploy_ prerequisite packages on your machine. In general,
most of this software should already be installed but some packages may not be.
It is therefore best to run this command before continuing.

    For Ubuntu 11.10:

        sudo apt-get --force-yes -y install python-dev libncurses5-dev libssl-dev libzmq-dev libgsl0-dev openjdk-6-jdk libxml2 libxslt1.1 libxslt1-dev ant git subversion build-essential zlib1g-dev libpng12-dev libfreetype6-dev mpich2 libreadline-dev gfortran unzip libmysqlclient16 libmysqlclient-dev ghc sqlite3 libsqlite3-dev libbz2-dev tcl-dev tk-dev r-base r-base-dev libatlas-dev libatlas-base-dev liblapack-dev swig libhdf5-serial-dev

    For Ubuntu 12.04 and Ubuntu 14.04:

        sudo apt-get --force-yes -y install python-dev libncurses5-dev libssl-dev libzmq-dev libgsl0-dev openjdk-6-jdk libxml2 libxslt1.1 libxslt1-dev ant git subversion build-essential zlib1g-dev libpng12-dev libfreetype6-dev mpich2 libreadline-dev gfortran unzip libmysqlclient18 libmysqlclient-dev ghc sqlite3 libsqlite3-dev libc6-i386 libbz2-dev tcl-dev tk-dev r-base r-base-dev libatlas-dev libatlas-base-dev liblapack-dev swig libhdf5-serial-dev

### Setting up qiime-deploy on CentOS and RedHat

Below is the summary of steps required for running _qiime-deploy_ on CentOS and RedHat (tested on CentOS 6.4):

1. Add the following repositories to your yum configuration directory (required to install ZeroMQ):

    For RHEL/CentOS 6:

        http://download.opensuse.org/repositories/home:/fengshuo:/zeromq/CentOS_CentOS-6/home:fengshuo:zeromq.repo

    This can be done by creating a file in /etc/yum.repos.d/, e.g., named zeromq.repo (requires admin (sudo) access). You can use your favorite text editor but we suggest _pico_ for simplicity. Note that at the bottom of the screen you will have the commands to save, exit, etc.

        sudo pico /etc/yum.repos.d/zeromq.repo

    Paste the following into that file:

    For RHEL/CentOS 6:

        [home_fengshuo_zeromq]
        name=The latest stable of zeromq builds (CentOS_CentOS-6)
        type=rpm-md
        baseurl=http://download.opensuse.org/repositories/home:/fengshuo:/zeromq/CentOS_CentOS-6/
        gpgcheck=1
        gpgkey=http://download.opensuse.org/repositories/home:/fengshuo:/zeromq/CentOS_CentOS-6/repodata/repomd.xml.key
        enabled=1

    Save and exit that file. Added repository will be used in the next step.

2. Install the _qiime-deploy_ dependencies on your machine. These steps require
admin (sudo) access. If you do not have sudo access, you must ask your system
administrator to grant you sudo access, or to run these commands for you.

        sudo yum groupinstall -y "development tools"

        sudo yum install -y ant compat-gcc-34-g77 java-1.6.0-openjdk java-1.6.0-openjdk-devel freetype freetype-devel zlib-devel mpich2 readline-devel zeromq zeromq-devel gsl gsl-devel libxslt libpng libpng-devel libgfortran mysql mysql-devel libXt libXt-devel libX11-devel mpich2 mpich2-devel libxml2 xorg-x11-server-Xorg dejavu* python-devel sqlite-devel tcl-devel tk-devel R R-devel ghc

### Installing requisite Python and R packages

Installing the latest version of QIIME (currently 1.9.0) using _qiime-deploy_ does not install Python, R, or their respective requisite packages (this behavior differs from how _qiime-deploy_ installed previous versions of QIIME). _qiime-deploy_ now assumes that a minimal (base) QIIME install exists. Follow the instructions [here](http://qiime.org/install/install.html#installing-qiime-natively-with-a-minimal-base-install) to obtain a minimal (base) QIIME install. Next, follow the instructions [here](http://qiime.org/install/install.html#r-install-notes) to install QIIME's requisite R packages. You're now ready to use _qiime-deploy_ to install QIIME's remaining dependencies.

## Common usage examples

The following subsections include examples of common _qiime-deploy_ use cases.

__Note:__ At the time of this writing, QIIME 1.9.1 is the latest public
release, and QIIME 1.9.1-dev is the development version of QIIME. As newer
versions of QIIME are released we will include conf files for each new version
in the
[qiime-deploy-conf project](https://github.com/qiime/qiime-deploy-conf). The
following usage examples will work for any version of QIIME (unless otherwise
noted), but you will need to supply the correct conf file as input to
_qiime-deploy_.

### Downloading qiime-deploy 

To get started please download 
the repositories listed below. These commands assume you have already set up your system
following the directions above and that you are in your home directory. 

    git clone git://github.com/qiime/qiime-deploy.git
    git clone git://github.com/qiime/qiime-deploy-conf.git
    cd qiime-deploy/
    
### View qiime-deploy options

To see the available options provided by qiime-deploy, run the following
command:

    python qiime-deploy.py -h

### Installing QIIME 1.9.1's dependencies

To install QIIME 1.9.1's dependencies under ```$HOME/qiime_software/```, run the
following commands. These commands assume you have already set up your system
following the directions above and that you are in your home directory. You can
change these paths as you like (e.g. to install QIIME's dependencies under a
different directory), but you will need to modify the commands we provide to use
the new paths.
    
    python qiime-deploy.py $HOME/qiime_software/ -f $HOME/qiime-deploy-conf/qiime-1.9.0/qiime.conf --force-remove-failed-dirs
    source $HOME/.bashrc

To test that you have a functioning QIIME install, run the following command:

    print_qiime_config.py -tf

_qiime-deploy_ will create a QIIME config file under
```$HOME/qiime_software/qiime_config``` as part of the deployment process. If
you would like to edit this file to further customize your QIIME install, feel
free to do so. If you rerun _qiime-deploy_ using the same deploy directory (in
this example, ```$HOME/qiime_software/```), your old QIIME config will be
renamed to ```qiime_config.bak``` and the new one will be named ```qiime_config```.

### Installing multiple versions of QIIME

You may install more than one version of QIIME's dependencies on your system. To
do so, you will need to install each version in its own deploy directory. For
example, if you would like to have both the dependencies for QIIME 1.9.1 and
QIIME 1.9.1-dev, you could install QIIME 1.9.1's dependencies under
```$HOME/qiime-1.9.1/``` and QIIME 1.9.1-dev's dependencies under
```$HOME/qiime-1.9.1-dev/```. To activate the QIIME version that you would like
to use, ```source``` the appropriate ```activate.sh``` file. For example, to
activate QIIME 1.9.1-dev, you would run the following command:

    source $HOME/qiime-1.9.1-dev/activate.sh

If you are unsure of what version of QIIME you currently have activated, run
the following command:

    print_qiime_config.py

### Changing QIIME versions

If you want to change the version of QIIME's dependencies in an __existing__
_qiime-deploy_ install, you can simply run _qiime-deploy_ with the conf file
corresponding to the version that you'd like to upgrade/downgrade to. Make sure
to specify the existing deploy directory in order to upgrade/downgrade your
existing install. If you specify a new directory, you will end up with multiple
versions of QIIME's dependencies installed on your system (which is okay; see
the section above for more details).

## Frequently Asked Questions

__When I run ```print_qiime_config.py -tf```, I get a test failure for
_usearch_. How can I fix this?__

_qiime-deploy_ cannot install _usearch_ due to licensing restrictions. You can
obtain the _usearch_ binary
[here](http://www.drive5.com/usearch/download.html). Please be sure to download
the currently supported version for your version of QIIME. If you are using the
latest stable release of QIIME, you can find the required _usearch_ version
[here](http://qiime.org/install/install.html).

Rename the executable to ```usearch``` and make sure it is somewhere that is in
your ```PATH``` environment variable. You also need to ensure that execute
permissions are set. For example:

    mkdir $HOME/bin
    mv <path to usearch executable> $HOME/bin/usearch
    chmod +x $HOME/bin/usearch
    echo 'export PATH=$HOME/bin:$PATH' >> $HOME/.bashrc
    (open a new terminal)
    usearch --version
    print_qiime_config.py -tf

__Does _qiime-deploy_ work on 32-bit operating systems?__

No, _qiime-deploy_ only supports 64-bit operating systems. If you run
_qiime-deploy_ on a 32-bit system, it may correctly install some dependencies,
but when running ```print_qiime_config.py -tf``` to check that your QIIME
install is functioning, you may receive strange errors similar to the
following:

    ELF : not found
    Syntax error: word unexpected (expecting ")")
    Syntax error: Unterminated quoted string

Upgrading your operating system to 64-bit and rerunning _qiime-deploy_ will
solve this issue.

## Contributing

1. New applications with custom build types should be added to
```lib/custom.py```. Both a function and a call to that function from
```custom.custom_deploy``` should be added.

2. Any custom finalization code should be called from ```lib/custom.py``` in ```custom.custom_finalize```.

3. If additional options need to be added to any of the config file sections,
they will likely need to be added to the init of the ```Application``` class in ```lib/application.py```.

4. New generic build processes will need to be added to the ```Application```
class in ```lib/application.py```. Additionally, the generic utility functions
required should be added to ```lib/util.py```.
