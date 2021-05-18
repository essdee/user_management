# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in user_management/__init__.py
from user_management import __version__ as version

setup(
	name='user_management',
	version=version,
	description='Frappe app to handle user management',
	author='Essdee',
	author_email='apps@essdee.dev',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
