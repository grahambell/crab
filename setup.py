#!/usr/bin/env python

from distutils.core import setup

with open('README') as file:
    long_description = file.read()

setup(name='Crab',
      version='0.0.0',
      author='Graham Bell',
      author_email='g.bell@jach.hawaii.edu',
      url='http://github.com/grahambell/crab',
      description='Cron alert board',
      long_description=long_description,
      package_dir={'': 'lib'},
      packages=[
                'crab',
                'crab.notify',
                'crab.report',
                'crab.service',
                'crab.store',
                'crab.util',
                'crab.web',
               ],
      scripts=[
               'scripts/crab',
               'scripts/crabd',
               'scripts/crabd-check',
               'scripts/crabsh',
               ],
      requires=[
                'CherryPy (>= 3.2.2)',
                'crontab (>= 0.14)',
                'Mako (>= 0.7.2)',
                'PyRSS2Gen (>= 1.0.0)',
                'pytz',
               ]
     )
