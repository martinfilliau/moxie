import os
from datetime import datetime

from fabric.api import *
from fabric.contrib import *
from fabric.contrib.files import exists, sed
from fabric import utils

_private_pypi = os.getenv('PRIVATE_PYPI')
PIP_OPTIONS = '-i %s' % _private_pypi if _private_pypi else ''

MOXIE_REPO = "git://github.com/ox-it/moxie.git"
MOXIE_CLIENT_REPO = "git://github.com/ox-it/moxie-js-client.git"

"""
This script has to be used as follow:
    first argument should be the target environment
    second argument should be the task to do (currently:
        * deploy
    )
"""

env.user = 'moxie'
env.remote_install_dir_api = '/srv/moxie/python-env'
env.remote_install_dir_front = '/srv/moxie/moxie-front'
env.restart_app_server = '/srv/moxie/reload-app-server'
env.remote_git_checkout_api = '/srv/moxie/moxie-api'
env.remote_git_checkout_front = '/srv/moxie/source-moxie-js'
env.additional_requirements = '/srv/moxie/requirements.txt'

"""
Methods
"""

def deploy_moxie_py(version):
    """
    Deploy mobileoxford (with given version - tag or branch) on defined
    environment in a virtual env
    """
    if not version:
        utils.abort('You must specify a version (whether branch or tag).')

    git_hash = git_branch(env.remote_git_checkout_api, MOXIE_REPO, version)

    versioned_path = '/srv/%s/moxie-%s-%s' % (env.user, datetime.now().strftime('%Y%m%d%H%M')
            , git_hash)

    createvirtualenv(versioned_path)
    with prefix('source %s' % os.path.join(versioned_path, 'bin', 'activate')):
        install_moxie()
        run('rm -f %s' % env.remote_install_dir_api)
        run('ln -s %s %s' % (versioned_path, env.remote_install_dir_api))

@task
def deploy_api(version):
    deploy_moxie_py(version)
    # uwsgi application server reloads when env.restart_app_server changes
    run('touch {reload_path}'.format(reload_path=env.restart_app_server))


@task
def deploy_tasks(version):
    deploy_moxie_py(version)
    run('supervisorctl restart moxie-celerybeat')
    run('supervisorctl restart moxie-celery')


@task
def deploy_front(version):
    """
    Deploy the front-end in a versioned folder and does a symlink
    """

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
        run('compass compile -e production --force')
        run('r.js -o app/moxie.build.js')
        # adding the URL of the git repo for the JS client as the first line of the built file
        run("sed -i '1s/^/\/\/ https:\/\/github.com\/ox-it\/moxie-js-client\\n/' app/main-built.js")
        sed("index-prod.html", "\{\{build\}\}", git_hash)
        FILES = [
            ('{path}/app/main-built.js', '{path}/app/main-built-{version}.js'),
            ('{path}/css/app.css', '{path}/css/app-{version}.css'),
            ('{path}/css/leaflet.css', '{path}/css/leaflet-{version}.css'),
            ('{path}/css/leaflet.ie.css', '{path}/css/leaflet.ie-{version}.css')
        ]
        for file in FILES:
            run('ln -s %s %s' % (file[0].format(path=versioned_path),
                                 file[1].format(path=versioned_path, version=git_hash)))

        run('ln -s %s %s' % ('index-prod.html', 'index.html'))

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
    if not console.confirm('Are you sure you want to delete all documents from this index?', default=False):
        utils.abort('Aborted.')
    run("curl http://localhost:8080/solr/{core}/update --data '<delete><query>*:*</query></delete>' -H 'Content-type:text/xml; charset=utf-8'".format(core=core))
    run("curl http://localhost:8080/solr/{core}/update --data '<commit/>' -H 'Content-type:text/xml; charset=utf-8'".format(core=core))


@task
def reload_core(core):
    """Reload core
    """
    if not core:
        utils.abort('You must specify the core')
    run("curl http://localhost:8080/solr/admin/cores?action=RELOAD&core={core}".format(core=core))


"""
Private methods
"""


def createvirtualenv(path):
    run('virtualenv %s' % path)


def install_moxie():
    with cd(env.remote_git_checkout_api):
        run('pip install . %s' % PIP_OPTIONS)
    run('pip install -r %s %s' % (env.additional_requirements, PIP_OPTIONS))


def git_branch(git_checkout, git_repo, name):
    """
    Do a checkout on a branch
    """
    if not exists(git_checkout):
        run('git clone %s %s' % (git_repo, git_checkout))

    with cd(git_checkout):
        run('git fetch origin')
        run('git checkout origin/%s' % name)
        run('git submodule update --init')
        return run('git rev-parse --short HEAD')
