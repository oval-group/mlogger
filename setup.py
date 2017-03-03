from setuptools import setup
from logger.main import __version__

setup(name='logger',
      description='A simple logger for experiments',
      author='Leonard Berrada',
      packages=['logger'],
      version=str(__version__),
      install_requires=["GitPython"])