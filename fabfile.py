import os
from datetime import datetime

from fabric.api import *
from fabric.contrib import *
from fabric.contrib.files import exists
from fabric import utils

MOXIE_REPO = "git://github.com/ox-it/moxie.git"

"""
This script has to be used as follow:
    first argument should be the target environment
    second argument should be the task to do (currently:
        * deploy
    )
"""

"""
Environments
"""

ENVIRONMENTS = ('dev', 'staging')

@task
def dev():
    """
    Configuration for Vagrant VMs (provisioned w/ Puppet)
    """
    env.environment = 'dev'
    env.hosts = ['33.33.33.10']
    env.user = 'moxie'
    env.remote_install_dir = '/srv/moxie/precise32.oucs.ox.ac.uk'
    env.remote_git_checkout = '/srv/moxie/source-moxie'


@task
def staging():
    """
    Configuration for api.m.ox.ac.uk
    """
    env.environment = 'staging'
    env.hosts = ['api.m.ox.ac.uk']
    env.user = 'moxie'
    env.remote_install_dir = '/srv/moxie/api.m.ox.ac.uk'
    env.remote_git_checkout = '/srv/moxie/source-moxie'


"""
Methods
"""


@task
def deploy(version):
    """
    Deploy mobileoxford (with given version - tag or branch) on defined
    environment in a virtual env
    """
    require('user', provided_by=ENVIRONMENTS)

    if not version:
        utils.abort('You must specify a version (whether branch or tag).')

    git_hash = git_branch(version)

    versioned_path = '/srv/%s/api-%s-%s' % (env.user, datetime.now().strftime('%Y%m%d%H%M')
            , git_hash)

    createvirtualenv(versioned_path)
    with prefix('source %s' % os.path.join(versioned_path, 'bin', 'activate')):
        install_moxie()
        run('rm -f %s' % env.remote_install_dir)
        run('ln -s %s %s' % (versioned_path, env.remote_install_dir))
        run('circusctl stop moxie-celery')
        run('circusctl start moxie-celery')
        run('circusctl stop moxie-uwsgi')
        run('circusctl start moxie-uwsgi')


"""
Private methods
"""

def createvirtualenv(path):
    run('virtualenv %s' % path)


def install_moxie():
    require('remote_git_checkout', provided_by=ENVIRONMENTS)
    with cd(env.remote_git_checkout):
        run('python setup.py install')


def git_check_existing_repo():
    """
    Checks that git repo exists, create it if it doesn't
    """
    if not exists(env.remote_git_checkout):
        run('git clone %s %s' % (MOXIE_REPO, env.remote_git_checkout))
        with cd(env.remote_git_checkout):
            run('git submodule init')


def git_branch(name):
    """
    Do a checkout on a branch
    """
    git_check_existing_repo()
    with cd(env.remote_git_checkout):
        run('git fetch origin')
        run('git checkout origin/%s' % name)
        run('git submodule update')
        return run('git rev-parse HEAD')


def git_tag(name):
    """
    Do a checkout on a tag (or commit's hash)
    """
    git_check_existing_repo()
    with cd(env.remote_git_checkout):
        run('git fetch origin')
        run('git checkout %s' % name)
        run('git submodule update')
        return name