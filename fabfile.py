import os
from datetime import datetime

from fabric.api import *
from fabric.contrib import *
from fabric.contrib.files import exists, sed
from fabric import utils

MOXIE_REPO = "git://github.com/ox-it/moxie.git"
MOXIE_CLIENT_REPO = "git://github.com/ox-it/moxie-js-client.git"

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
    env.hosts = ['new-mox.vm']
    env.user = 'moxie'
    env.remote_install_dir_api = '/srv/moxie/precise32.oucs.ox.ac.uk'
    env.remote_git_checkout_api = '/srv/moxie/source-moxie'
    env.remote_install_dir_front = '/srv/moxie/js.mox'
    env.remote_git_checkout_front = '/srv/moxie/source-moxie-js'
    env.additional_requirements = '/srv/moxie/requirements.txt'


@task
def staging():
    """
    Configuration for api.m.ox.ac.uk
    """
    env.environment = 'staging'
    env.hosts = ['api.m.ox.ac.uk']
    env.user = 'moxie'
    env.remote_install_dir_api = '/srv/moxie/torvalds.oucs.ox.ac.uk'
    env.remote_git_checkout_api = '/srv/moxie/moxie-api'
    env.remote_install_dir_front = '/srv/moxie/new.m.ox.ac.uk'
    env.remote_git_checkout_front = '/srv/moxie/moxie-js'
    env.additional_requirements = '/srv/moxie/requirements.txt'


"""
Methods
"""


@task
def deploy_api(version):
    """
    Deploy mobileoxford (with given version - tag or branch) on defined
    environment in a virtual env
    """
    require('user', provided_by=ENVIRONMENTS)

    if not version:
        utils.abort('You must specify a version (whether branch or tag).')

    git_hash = git_branch(env.remote_git_checkout_api, MOXIE_REPO, version)

    versioned_path = '/srv/%s/api-%s-%s' % (env.user, datetime.now().strftime('%Y%m%d%H%M')
            , git_hash)

    createvirtualenv(versioned_path)
    with prefix('source %s' % os.path.join(versioned_path, 'bin', 'activate')):
        install_moxie()
        run('rm -f %s' % env.remote_install_dir_api)
        run('ln -s %s %s' % (versioned_path, env.remote_install_dir_api))
        run('circusctl stop moxie-celery')
        run('circusctl start moxie-celery')
        run('circusctl stop moxie-uwsgi')
        run('circusctl start moxie-uwsgi')


@task
def deploy_front(version):
    """
    Deploy the front-end in a versioned folder and does a symlink
    """

    require('user', provided_by=ENVIRONMENTS)

    if not version:
        utils.abort('You must specify a version (whether branch or tag).')

    git_hash = git_branch(env.remote_git_checkout_front,
            MOXIE_CLIENT_REPO, version)
    versioned_path = '/srv/%s/client-%s-%s' % (
            env.user, datetime.now().strftime('%Y%m%d%H%M'), git_hash)
    run('mkdir {0}'.format(versioned_path))
    run('cp -R {0}/* {1}'.format(
        env.remote_git_checkout_front, versioned_path))
    with(cd(versioned_path)):
        run('compass compile')
        run('r.js -o app/moxie.build.js')
        sed("index-prod.html", "\{\{build\}\}", git_hash)
        if env.environment in ['staging', 'production']:
            run('ln -s %s %s' % ('index-prod.html', 'index.html'))
        else:
            run('ln -s %s %s' % ('index-dev.html', 'index.html'))
    # Pre GZip static (html, css, js) files
    run('sh {0}/gzip_static_files.sh {1}'.format(
        env.remote_git_checkout_front, versioned_path))
    run('rm -f %s' % env.remote_install_dir_front)
    run('ln -s %s %s' % (versioned_path, env.remote_install_dir_front))


@task
def delete_index(core):
    """Delete all documents from a Solr index 
    """
    if not core:
        utils.abort('You must specify the core')
    run("curl http://localhost:8080/solr/{core}/update --data '<delete><query>*:*</query></delete>' -H 'Content-type:text/xml; charset=utf-8'".format(core=core))
    run("curl http://localhost:8080/solr/{core}/update --data '<commit/>' -H 'Content-type:text/xml; charset=utf-8'".format(core=core))


"""
Private methods
"""


def createvirtualenv(path):
    run('virtualenv --extra-search-dir=/usr/share/moxie-virtualenv %s' % path)


def install_moxie():
    require('remote_git_checkout_api', provided_by=ENVIRONMENTS)
    run('pip install wheel')
    run('pip install -U distribute>=0.6.34')
    with cd(env.remote_git_checkout_api):
        run('pip wheel --wheel-dir=/tmp/wheelhouse -r requirements.txt')
        run('pip install --use-wheel --no-index --find-links=/tmp/wheelhouse .')
    run('pip wheel --wheel-dir=/tmp/wheelhouse -r %s' % env.additional_requirements)
    run('pip install --use-wheel --no-index --find-links=/tmp/wheelhouse -r %s' % env.additional_requirements)


def git_branch(git_checkout, git_repo, name):
    """
    Do a checkout on a branch
    """
    if not exists(git_checkout):
        run('git clone %s %s' % (git_repo, git_checkout))

    with cd(git_checkout):
        run('git fetch origin')
        run('git checkout origin/%s' % name)
        return run('git rev-parse HEAD')
