#!/usr/bin/env python

from setuptools import setup

with open('parxiv.py') as f:
    for line in f:
        if line.startswith('__version__'):
            version = eval(line.split('=')[-1])

long_description = open('README.md').read()

setup(name='parxiv',
      license='MIT',
      version=version,
      description='Generate a clean directory for uploading to Arxiv (formerly clean-latex-to-arxiv).',
      long_description=long_description,
      author='Luke Olson',
      author_email='luke.olson@gmail.com',
      url='https://github.com/lukeolson/parxiv',
      py_modules=['parxiv'],
      install_requires=['ply'],
      entry_points={'console_scripts': ['parxiv = parxiv:main']},
      classifiers=['Environment :: Console',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 3',
                   'Topic :: Utilities'])
