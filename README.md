# qiime-deploy

A Python application to build, configure, and deploy QIIME and its
dependencies on Linux systems.

## Getting started

To run _qiime-deploy_, you will first need to grab a configuration file. The
configuration file will tell _qiime-deploy_ what packages it should install.
You can find many QIIME deployment configuration files in the
_qiime-deploy-conf_ project [here](https://github.com/qiime/qiime-deploy-conf)
as well as a description of all possible options and the configuration file
format. There are also various other configuration files included for
installing other QIIME-related projects/tools.

Also, while _qiime-deploy_ downloads, builds, and installs many of QIIME's
dependencies, it does expect common packages to already be installed on your
system. For example, on Debian Lenny, a complete QIIME install depends on the
following packages:

    libgsl0-dev openjdk-6-jdk libxml2 libxslt1.1 libxslt1-dev ant git
    subversion build-essential zlib1g-dev libpng12-dev libfreetype6-dev mpich2
    libreadline-dev gfortran unzip libmysqlclient16 libmysqlclient-dev ghc
    python-dev libncurses5-dev

After the deploy completes it will generate an ```activate.sh``` file in the
base deploy directory. It is necessary to ```source``` that file in order to
set the environment created by _qiime-deploy_. For example, if the deploy
directory is ```/opt/qiime/``` you will need to run the following command:

    $ source /opt/qiime/activate.sh

__Note:__ By default, _qiime-deploy_ will append the above line to your
```~/.bashrc```. This is done so that you do not need to run the command
each time you open a new terminal. To disable this behavior, you will need to
modify the _qiime-deploy_ conf file (see the _qiime-deploy-conf_ project
[here](https://github.com/qiime/qiime-deploy-conf) for a description of the
options you can tweak).

## Setting up qiime-deploy on Ubuntu

While _qiime-deploy_ may work on various Linux distributions, it has been most
heavily tested on Ubuntu 11.10 and 12.04 LTS (64-bit) systems. Thus,
we provide a short guide to setting up your Ubuntu system so that it can run
_qiime-deploy_.

In order to ensure that you have the required prerequisite packages installed
on your Ubuntu system, perform the following steps:

1. Uncomment the universe and multiverse repositories from
```/etc/apt/sources.list```. You can use your favorite text editor but we
suggest _pico_ for simplicity. Note that at the bottom of the screen you
will have the commands to save, exit, etc..

        $ sudo pico /etc/apt/sources.list

2. Install the _qiime-deploy_ dependencies on your machine. This step requires
admin (sudo) access. If you do not have sudo access, you must ask your system
administrator to grant you sudo access, or to run these steps for you. In
general, all of this software should already be installed but it may not be.
It's therefore best to run this command before the following step.

    For Ubuntu 11.10:

        $ sudo apt-get --force-yes -y install python-dev libncurses5-dev libssl-dev libzmq-dev libgsl0-dev openjdk-6-jdk libxml2 libxslt1.1 libxslt1-dev ant git subversion build-essential zlib1g-dev libpng12-dev libfreetype6-dev mpich2 libreadline-dev gfortran unzip libmysqlclient16 libmysqlclient-dev ghc

    For Ubuntu 12.04:
 
        $ sudo apt-get --force-yes -y install python-dev libncurses5-dev libssl-dev libzmq-dev libgsl0-dev openjdk-6-jdk libxml2 libxslt1.1 libxslt1-dev ant git subversion build-essential zlib1g-dev libpng12-dev libfreetype6-dev mpich2 libreadline-dev gfortran unzip libmysqlclient18 libmysqlclient-dev ghc

## Common usage examples

The following subsections include examples of common _qiime-deploy_ use cases.

__Note:__ At the time of this writing, QIIME 1.5.0 is the latest public
release, and QIIME 1.5.0-dev is the development version of QIIME. As newer
versions of QIIME are released we will include conf files for each new version
in the
[qiime-deploy-conf project](https://github.com/qiime/qiime-deploy-conf). The
following usage examples will work for any version of QIIME (unless otherwise
noted), but you will need to supply the correct conf file as input to
_qiime-deploy_.

### View qiime-deploy options

To see the available options provided by qiime-deploy, run the following
command:

    $ python qiime-deploy.py -h

### Installing QIIME 1.5.0 (stable public release)

To install QIIME 1.5.0 under ```$HOME/qiime_software/```, run the following
commands. These commands assume you have already set up your system following
the directions above and that you are in your home directory. You can change
these paths as you like (e.g. to install QIIME under a different directory),
but you will need to modify the commands we provide to use the new paths.

    $ git clone git://github.com/qiime/qiime-deploy.git
    $ git clone git://github.com/qiime/qiime-deploy-conf.git
    $ cd qiime-deploy/
    $ python qiime-deploy.py $HOME/qiime_software/ -f $HOME/qiime-deploy-conf/qiime-1.5.0/qiime.conf --force-remove-failed-dirs
    $ source $HOME/.bashrc

To test that you have a functioning QIIME install, run the following command:

    $ print_qiime_config.py -t

_qiime-deploy_ will create a QIIME config file under
```$HOME/qiime_software/qiime_config``` as part of the deployment process. If
you would like to edit this file to further customize your QIIME install, feel
free to do so. If you rerun _qiime-deploy_ using the same deploy directory (in
this example, ```$HOME/qiime_software/```), your old QIIME config will be
renamed to ```qiime_config.bak``` and the new one will be named ```qiime_config```.

### Installing QIIME 1.5.0-dev

To install the development version of QIIME (currently 1.5.0-dev), use the same
commands as above, but supply a different _qiime-deploy_ conf file as input:

    $ python qiime-deploy.py $HOME/qiime_software/ -f $HOME/qiime-deploy-conf/qiime-1.5.0-dev/qiime.conf --force-remove-failed-dirs --force-remove-previous-repos

### Installing multiple versions of QIIME

You may install more than one version of QIIME on your system. To do so, you
will need to install each version in its own deploy directory. For example, if
you would like to have QIIME 1.5.0 and QIIME 1.5.0-dev, you could install
QIIME 1.5.0 under ```$HOME/qiime-1.5.0/``` and QIIME 1.5.0-dev under
```$HOME/qiime-1.5.0-dev/```. To activate the QIIME version that you would like
to use, ```source``` the appropriate ```activate.sh``` file. For example, to
activate QIIME 1.5.0-dev, you would run the following command:

    $ source $HOME/qiime-1.5.0/activate.sh

If you are unsure of what version of QIIME you currently have activated, run
the following command:

    $ print_qiime_config.py -t

### Changing QIIME versions

If you want to change the version of QIIME in an __existing__ _qiime-deploy_
install, you can simply run _qiime-deploy_ with the conf file corresponding to
the version that you'd like to upgrade/downgrade to. Make sure to specify the
existing deploy directory in order to upgrade/downgrade your existing install.
If you specify a new directory, you will end up with multiple versions of QIIME
installed on your system (which is okay; see the section above for more
details).

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
