#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Octowire Framework
# Copyright (c) Jordan Ovrè / Paul Duncan
# License: GPLv3
# Paul Duncan / Eresse <eresse@dooba.io>
# Jordan Ovrè / Ghecko <ghecko78@gmail.com


from setuptools import setup, find_packages

description = 'Octowire Framework flash dump module'
name = 'owfmodules.spi.flash_dump'
setup(
    name=name,
    version='1.0.0',
    packages=find_packages(),
    license='GPLv3',
    description=description,
    author="Jordan Ovrè , Paul Duncan",
    url='https://bitbucket.org/octowire/' + name,
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha'
    ],
    keywords=['octowire', 'framework', 'hardware', 'security', 'spi', 'dump', 'flash', 'memory']
)