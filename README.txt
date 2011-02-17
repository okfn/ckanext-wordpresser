A CKAN extension for underlaying Wordpress content (navigation and
content area) in your CKAN site.

For example, if you make a new Page in your Wordpress site called
"Resources", that will be appended to your CKAN navigation.

WARNING: this is a rough, unparameterized first draft.

Installation
============

1. Install the extension as usual, e.g.

  ::

    $ pip install -e  hg+https://bitbucket.org/sebbacon/ckanext-wordpresser#package=/ckanext-wordpresser

2. Set up a Wordpress site (e.g. at wordpress.com) and add a Page or two

3. Edit your development.ini (or similar) with:

  ::

      wordpresser.proxy_host = http://<yoursite>.wordpress.com/

4. Marvel at the appearance of Wordpress pages within your CKAN instance

TODO
====

* Cache the Wordpress nav so we aren't round-tripping to a proxy
  server on each request
