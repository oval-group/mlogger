from setuptools import setup, find_packages

__version__ = "1.0.1a"

setup(name='mlogger',
      description='A Machine Learning logger',
      author='Leonard Berrada',
      packages=find_packages(),
      license="MIT License",
      url='https://github.com/oval-group/mlogger',
      version=str(__version__),
      install_requires=["GitPython",
                        "numpy",
                        "future"])
