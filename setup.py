from distutils.core import setup
import setuptools

setup(
    name='GraphWaveFunctionCollapse',
    version='0.9.0',
    description='Colors a networkx (Di)Graph based on patterns extracted from an colored example (Di)Graph',
    packages=['graphwfc',],
    install_requires=[
          'networkx',
      ],
    python_requires=">=3.0",
    url='http://github.com/lamelizard/graphwavefunctioncollapse',
    license='MIT',
    long_description=open('README.md').read(),
)