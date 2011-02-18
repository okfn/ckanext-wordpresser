import logging

log = logging.getLogger(__name__)
from lxml.html import tostring, fromstring
from webob import Request
import paste.proxy
from pylons.controllers.util import redirect
from pylons import request
from genshi.filters.transform import Transformer
from genshi.input import HTML

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IConfigurable, IGenshiStreamFilter


class WordpresserException(Exception): pass


class Wordpresser(SingletonPlugin):
    implements(IConfigurable, inherit=True)
    implements(IGenshiStreamFilter)

    def configure(self, config):
        self.config = config
        log.info("Loading Wordpresser extension")
        if not 'wordpresser.proxy_host' in config:
            msg = "Must have 'wordpresser.proxy_host in config"
            raise WordpresserException(msg)

    def filter(self, stream):
        original_response = request.environ.get('pylons.original_response')
        original_req = request.environ.get('pylons.original_request')
        proxy_host = self.config.get('wordpresser.proxy_host')

        # grab the WP page -- we always need it for the nav, at least,
        # and optionally for content when we get a 404 from CKAN.
        environ = original_req and original_req.environ or request.environ
        req = Request(environ)
        req.remove_conditional_headers(remove_encoding=True)
        follow = True
        proxy_url = proxy_host

        while follow:
            # deal with redirects internal to Wordpress
            wp_resp = req.get_response(paste.proxy.Proxy(proxy_url))
            follow = wp_resp.status_int == 301 \
                     and proxy_host in wp_resp.location
            environ['PATH_INFO'] = ''
            proxy_url = wp_resp.location
            req = Request(environ)
        #request.environ['PATH_INFO'] = path_info
        if wp_resp.status_int == 500:
            pass  # validation errors etc
        if wp_resp.status_int in [301, 302]:
            if proxy_host in wp_resp.location:
                wp_resp.location = wp_resp.location.replace(proxy_host,
                                                            req.host_url + "/")
            redirect(wp_resp.location, code=wp_resp.status_int)
        wp_resp.decode_content()
        wp_etree = fromstring(wp_resp.body)

        # append WP nav onto CKAN nav
        wp_nav = wp_etree.xpath('//div[contains(@class,"menu")]/ul/li')
        wp_nav = "".join([tostring(item) for item in wp_nav])
        if wp_nav.strip():
            stream = stream | Transformer('//div[@class="menu"]/ul')\
                     .append(HTML(wp_nav))
        # insert WP content into CKAN content area, if required
        if original_response and original_response.status_int >= 400:
            if wp_resp.status_int == 404:
                # Return our local 'not found' error
                proxy_content = ""
            elif wp_resp.status_int >= 400:
                # return Wordpress error
                wp_error = wp_etree.xpath('//body[@id="error-page"]')
                # set Wordpress' error text to be wrapped in our content div
                proxy_content = wp_error[0]
                proxy_content.tag = "div"
                proxy_content.attrib['id'] = "content"
                proxy_content = tostring(proxy_content)
            else:
                proxy_content = wp_etree.xpath(
                    '//div[@id="content"]')[0]
                proxy_content = tostring(proxy_content)
                proxy_title = tostring(wp_etree.xpath('//title')[0])
            if proxy_content:
                stream = stream | Transformer('//div[@id="content"]')\
                         .replace(HTML(proxy_content))
                stream = stream | Transformer('//title')\
                         .replace(HTML(proxy_title))
                

        def replace_host(name, event):
            attrs = event[1][1]
            return attrs.get(name).replace(proxy_host, "/")

        stream = stream | Transformer("//a[contains(@href,'%s')]" \
                                      % proxy_host)\
                 .attr('href', replace_host)
        stream = stream | Transformer("//form[contains(@action,'%s')]"\
                                      % proxy_host)\
                 .attr('action', replace_host)
        return stream
