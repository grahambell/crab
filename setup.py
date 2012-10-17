#!/usr/bin/env python

import os
from distutils.core import setup

with open('README.rst') as file:
    long_description = file.read()

def find_packages(base, path=[]):
    """Search for Python pacakges in the directory 'base'.
    Package names are built from the path components given
    by 'path'."""
    packages = []

    for name in os.listdir(os.path.join(base, *path)):
        pathname = path + [name]
        pathname_ = os.path.join(base, *pathname)

        if os.path.islink(pathname_):
            pass
        elif name == '__init__.py':
            packages.append('.'.join(path))
        elif os.path.isdir(pathname_):
            packages.extend(find_packages(base, pathname))

    return packages

def find_files(inst, base=None, path=[]):
    """Search for data files in directory 'base', starting at 'path'.
    Files are to be installed in directory 'inst'.  The 'base'
    directory name is not included in the install path."""
    files = []
    subdirs = []

    if base:
        fullpath = os.path.join(base, *path)
    else:
        fullpath = os.path.join(*path)

    for name in os.listdir(fullpath):
        pathname = path + [name]
        pathname_ = os.path.join(fullpath, name)

        if os.path.islink(pathname_):
            pass
        elif os.path.isdir(pathname_):
            subdirs.extend(find_files(inst, base, pathname))
        else:
            files.append(pathname_)

    if files:
        subdirs.append((os.path.join(inst, *path), files))

    return subdirs

setup(name='crab',
      version='0.2.0',
      author='Graham Bell',
      author_email='g.bell@jach.hawaii.edu',
      url='http://github.com/grahambell/crab',
      description='Cron alert board',
      long_description=long_description,
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      scripts=[os.path.join('scripts', script) for script in [
                   'crab',
                   'crabd',
                   'crabd-check',
                   'crabsh',
              ]],
      data_files=find_files(os.path.join('share', 'doc', 'crab'), 'doc') +
                 find_files(os.path.join('share', 'crab'), None, ['res']) +
                 find_files(os.path.join('share', 'crab'), None, ['templ']),
      requires=[
                'CherryPy (>= 3.2.2)',
                'crontab (>= 0.15)',
                'Mako (>= 0.7.2)',
                'PyRSS2Gen (>= 1.1)',
                'pytz',
               ],
      classifiers=[
                   'Development Status :: 3 - Alpha',
                   'License :: OSI Approved :: GNU General Public License '
                                               'v3 or later (GPLv3+)',
                   'Programming Language :: Python',
                   'Topic :: System :: Monitoring'
                  ]
     )
