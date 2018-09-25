from setuptools import setup

setup(
    name='GraphWFC',
    version='0.9.3',
	author="lamelizard",
    author_email="florian.drux@rwth-aachen.de",
    description='Colors a networkx (Di)Graph based on patterns extracted from an colored example (Di)Graph',
    packages=['graphwfc',],
    install_requires=[
          'networkx',
      ],
    python_requires=">=3.0",
    url='https://github.com/lamelizard/GraphWaveFunctionCollapse',
    license='MIT',
    long_description="A python 3.x package to color a graph based on patterns extracted from an colored example graph. More infos on https://github.com/lamelizard/GraphWaveFunctionCollapse",
)