import logging
import os

log = logging.getLogger(__name__)

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IConfigurable, IMiddleware, IConfigurer

from ckanext.wordpresser.middleware import WordpresserMiddleware


class WordpresserException(Exception): pass


class Wordpresser(SingletonPlugin):
    implements(IConfigurable, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IMiddleware, inherit=True)

    def configure(self, config):
        self.config = config
        log.info("Loading Wordpresser extension")
        if not 'wordpresser.proxy_host' in config:
            msg = "Must have 'wordpresser.proxy_host in config"
            raise WordpresserException(msg)

    def update_config(self, config):
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        template_dir = os.path.join(rootdir, 'ckanext', 'wordpresser', 'theme', 'templates')
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])


    def make_middleware(self, app, config):
        return WordpresserMiddleware(app)
