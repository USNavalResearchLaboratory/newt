#!/usr/bin/env python

import os
from setuptools import setup, find_packages

package = __import__('newt')

setup(name='newt',
      install_requires=['distribute'], # let's require the enhanced setuptools
      version=package.get_version(),
      license='BSD',
      description=package.__doc__.strip(),
      author='Ian Taylor',
      author_email='ian.j.taylor@gmail.com',
      url='https://www.python.org/newt/',
      include_package_data=True, # this will use MANIFEST.in during install where we specify additional files
      packages=find_packages(),
      scripts=[],
      requires=[],
)


os.system ('rm -rf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')
