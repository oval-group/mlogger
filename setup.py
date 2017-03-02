from distutils.core import setup
from logger.main import __version__

setup(name='logger',
      description='A minimalist logger for experiments',
      author='Leonard Berrada',
      packages=['logger'],
      version=str(__version__),
      install_requires=["cPickle, GitPython"])