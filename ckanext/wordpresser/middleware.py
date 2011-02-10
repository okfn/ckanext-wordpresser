import paste.proxy
from paste.deploy.converters import asbool
from lxml.html import tostring, fromstring
from ckan.lib.base import render
from webob import Request
import pylons
from pylons.wsgiapp import PylonsApp
from pylons.controllers.util import abort


class WordpresserException(Exception): pass


class WordpresserMiddleware(object):
    def __init__(self, app, config=None):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        proxy_host = self.config.get('wordpresser.proxy_host')

        # grab the WP page -- we always need it for the nav, at least,
        # and optionally for content when we get a 404 from CKAN.
        req = Request(environ)
        req.remove_conditional_headers(remove_encoding=True)
        follow = True
        proxy_url = proxy_host
        path_info = environ['PATH_INFO']
        while follow:
            # deal with redirects internal to Wordpress
            wp_resp = req.get_response(paste.proxy.Proxy(proxy_url))
            follow = wp_resp.status_int == 301 \
                     and proxy_host in wp_resp.location
            environ['PATH_INFO'] = ''
            proxy_url = wp_resp.location
        environ['PATH_INFO'] = path_info
        if wp_resp.status_int == 500:
            pass  # validation errors etc
        if wp_resp.status_int in [301, 302]:
            if proxy_host in wp_resp.location:
                wp_resp.location = wp_resp.location.replace(proxy_host,
                                                            req.host_url + "/")
            return wp_resp(req.environ, start_response)
        wp_resp.decode_content()
        wp_etree = fromstring(wp_resp.body)

        # now try getting CKAN page
        req = Request(environ)
        ckan_resp = req.get_response(self.app)
        if ckan_resp.status_int in [301, 302, 401]:
            return ckan_resp(environ, start_response)
        ckan_error = None
        if ckan_resp.status_int >= 400:
            # we don't necessarily get an attractive 404 page due to
            # the order of the middleware, so we grab the index
            # template instead and put the error in that
            ckan_error = fromstring(ckan_resp.body).xpath('//body')
            pylons_app = PylonsApp()
            pylons_app.setup_app_env(environ, start_response)
            registry = environ['paste.registry']
            registry.register(pylons.request, req)
            registry.register(pylons.response, ckan_resp)
            ckan_etree = fromstring(render('home/index.html'))
        else:
            # We're going to use the content we got from CKAN
            ckan_etree = fromstring(ckan_resp.body)

        # append WP nav onto CKAN nav
        wp_nav = wp_etree.xpath('//div[@class="menu"]/ul/*')
        ckan_etree_nav = ckan_etree.xpath('//div[@class="menu"]/ul')
        if ckan_etree_nav:
            ckan_etree_nav[0].extend(wp_nav)

        # insert WP content into CKAN content area, if required
        if ckan_resp.status_int >= 400:
            if wp_resp.status_int == 404:
                # Return our local 'not found' error
                proxy_content = ckan_error[0]
                proxy_content.tag = "div"
                proxy_content.attrib['id'] = "content"
            elif wp_resp.status_int >= 400:
                # return Wordpress error
                wp_error = wp_etree.xpath('//body[@id="error-page"]')
                # set Wordpress' error text to be wrapped in our content div
                proxy_content = wp_error[0]
                proxy_content.tag = "div"
                proxy_content.attrib['id'] = "content"
            else:
                proxy_content = wp_etree.xpath(
                    '//div[@id="content"]')[0]
            ckan_etree_content = ckan_etree.xpath(
                    '//div[@id="content"]')[0]
            ckan_etree_content_container = ckan_etree_content.getparent()
            ckan_etree_content_container.remove(ckan_etree_content)
            ckan_etree_content_container.append(proxy_content)

        output = tostring(ckan_etree)
        output = output.replace(proxy_host, "/")
        start_response("200 OK", [('Content-Type', 'text/html'),
                                  ('Content-Length', str(len(output)))])
        return [output]
