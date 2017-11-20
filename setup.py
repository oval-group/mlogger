from setuptools import setup

__version__ = 0.3

setup(name='logger',
      description='A simple logger for experiments',
      author='Leonard Berrada',
      packages=['logger'],
      license="MIT License",
      url='https://github.com/oval-group/logger',
      version=str(__version__),
      install_requires=["GitPython",
                        "numpy",
                        "future"])
