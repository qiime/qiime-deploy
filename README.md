qiime-deploy
============

A Python application to build, configure, and deploy QIIME's dependencies.

Getting started
---------------

To run qiime-deploy, you will first need to grab a configuration file. You can
find many QIIME deployment configuration files here:
github.com/qiime/qiime-deploy-conf as well as a description of all possible
options and the configuration file format.

Also, while qiime-deploy downloads, builds, and installs many of QIIME's
dependencies, it does expect common packages to already be installed. For
example, on Debian Lenny, a complete QIIME install depends on the following
packages:

    libgsl0-dev openjdk-6-jdk libxml2 libxslt1.1 libxslt1-dev ant subversion 
    build-essential zlib1g-dev libpng12-dev libfreetype6-dev mpich2 
    libreadline-dev gfortran unzip libmysqlclient16 libmysqlclient-dev ghc

After the deploy completes it will generate an activate.sh file in the base
deploy directory. It is necessary to source that file in order to set the
environment created by qiime-deploy, e.g.:

    source /opt/qiime/activate.sh

Usage
-----

    python qiime-deploy.py -h

Contributing
------------

1. New applications with custom build types should be added to lib/custom.py.
Both a function and a call to that function from custom\_deploy should be
added.

2. Any custom finalization code should be called from lib/custom.py in
custom\_finalize.

3. If additional options need to be added to any of the config file sections,
they will likely need to be added to the init of the Application class in
lib/application.py

4. New generic build processes will need to be added to the Application class
in lib/application.py. Additionally, the generic utility functions required
should be added to lib/util.py.
