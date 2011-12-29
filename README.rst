A CKAN extension for underlaying Wordpress content (navigation and
content area) in your CKAN site.

For example, if you make a new Page in your Wordpress site called
"Resources", that will be appended to your CKAN navigation.

Any page that would normally result in a 404 from CKAN will then be
checked for existence in Wordpress before returning to the user.

This only works against CKAN 1.3.1 or newer.

Installation
============

1. Install the extension as usual, e.g.::

    $ pip install -e  git+https://github.com/okfn/ckanext-wordpresser#egg=ckanext-wordpresser

2. Set up a Wordpress site (e.g. at wordpress.com) and add a Page or
   two to the primary navigation.  Note that this has only been tested
   with Wordpress 3.1 and the Twenty Ten theme.

3. Ensure Wordpress is set up to use permalinks (e.g. the "Numeric"
   setting at Settings -> Permalinks)

4. Edit your development.ini (or similar) with::

    ckan.plugins = wordpresser   # and your other plugins...
    wordpresser.proxy_host = http://<yoursite>.wordpress.com/

5. Marvel at the appearance of Wordpress pages within your CKAN instance


Running tests
-------------

With your ckan virtualenv activated, run the following command from within pyenv/src/ckan::

  nosetests --ckan ../ckanext-wordpresser/tests

