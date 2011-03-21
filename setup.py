from setuptools import setup, find_packages
import sys, os

version = '0.11'

setup(
	name='ckanext-wordpresser',
	version=version,
	description="Extend CKAN content with content from Wordpress",
	long_description="""\
        This CKAN extension allows you to overlay the standard CKAN
	navigation with extra content proxied from a Wordpress
	installation, bringing CMS capabilities to your CKAN install.
	You can also use it to create a blog page, enable comments, etc.
	""",
	classifiers=["Development Status :: 2 - Pre-Alpha",
                     "Framework :: Pylons"], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='wordpress wsgi middleware ckan',
	author='Seb Bacon',
	author_email='seb.bacon@okfn.org',
	url='',
	license='GPL',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.wordpresser'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
                'lxml',
                'webob',
                'httpencode'
	],
	entry_points=\
	"""
        [ckan.plugins]
	wordpresser=ckanext.wordpresser:Wordpresser
	""",
)
