A CKAN extension for underlaying Wordpress content (navigation and
content area) in your CKAN site.

For example, if you make a new Page in your Wordpress site called
"Resources", that will be appended to your CKAN navigation.

Any page that would normally result in a 404 from CKAN will then be
checked for existence in Wordpress before returning to the user.

This only works against CKAN 1.3.1 or newer.

Installation
============

1. Install the extension as usual, e.g.

  ::

    $ pip install -e  hg+https://bitbucket.org/sebbacon/ckanext-wordpresser#package=/ckanext-wordpresser

2. Set up a Wordpress site (e.g. at wordpress.com) and add a Page or
two to the primary navigation

3. Edit your development.ini (or similar) with:

  ::

      wordpresser.proxy_host = http://<yoursite>.wordpress.com/

4. Marvel at the appearance of Wordpress pages within your CKAN instance


Running tests
-------------

With your ckan virtualenv activated, run the following command from within pyenv/src/ckan:

    nosetests --ckan ../ckanext-wordpresser/tests
