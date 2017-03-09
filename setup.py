from setuptools import setup

__version__ = 0.1

setup(name='logger',
      description='A simple logger for experiments',
      author='Leonard Berrada',
      packages=['logger'],
      version=str(__version__),
      install_requires=["GitPython"])
