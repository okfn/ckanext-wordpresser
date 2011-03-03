import logging

log = logging.getLogger(__name__)

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IConfigurable, IMiddleware

from ckanext.wordpresser.middleware import WordpresserMiddleware


class WordpresserException(Exception): pass


class Wordpresser(SingletonPlugin):
    implements(IConfigurable, inherit=True)
    implements(IMiddleware, inherit=True)

    def configure(self, config):
        self.config = config
        log.info("Loading Wordpresser extension")
        if not 'wordpresser.proxy_host' in config:
            msg = "Must have 'wordpresser.proxy_host in config"
            raise WordpresserException(msg)

    def make_middleware(self, app, config):
        return WordpresserMiddleware(app)
