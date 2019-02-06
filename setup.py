from setuptools import setup

__version__ = "1.0a"

setup(name='mlogger',
      description='A Machine Learning logger',
      author='Leonard Berrada',
      packages=['mlogger'],
      license="MIT License",
      url='https://github.com/oval-group/mlogger',
      version=str(__version__),
      install_requires=["GitPython",
                        "numpy",
                        "future"])
