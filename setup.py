from setuptools import setup, find_packages


install_requires = open('requirements.txt').readlines()

setup(name='moxie',
        version='0.1',
        packages=find_packages(),
        description='The new Mobile Oxford',
        author='Mobile Oxford',
        author_email='mobileoxford@oucs.ox.ac.uk',
        url='https://github.com/ox-it/moxie',
        setup_requires=["setuptools"],
        install_requires=install_requires,
        tests_require=['mock'],
        test_suite="moxie.tests",
        )
