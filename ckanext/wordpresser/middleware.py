from lxml.html import tostring, fromstring
from webob import Request
import paste.proxy
from paste.wsgilib import encode_unicode_app_iter
from pylons.util import call_wsgi_application
from pylons import config
from httpencode.wrappers import FileAppIterWrapper
from pylons.decorators.cache import beaker_cache

from ckan.lib.base import render


STATUS_KEY = 'ckanext.wordpresser.wp_status'


class WordpresserMiddleware(object):
    """When we rewrite the content of the page, we also want to reset
    the status code.  This has to be done in middleware.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        '''WSGI Middleware that renders the page as usual, then
        transcludes some of the content from a Wordpress proxy.
        '''
        # get our content
        status, headers, app_iter, exc_info = call_wsgi_application(
            self.app, environ, catch_exc_info=True)
        if environ['REQUEST_METHOD'] in ['GET', 'POST'] \
               and not status.startswith('304 '):
            # make sure it's unicode
            content = FileAppIterWrapper(app_iter).read()
            charset = "utf-8"
            for k, v in headers:
                if k.lower() == "content-type":
                    charset_pos = v.find("charset")
                    if charset_pos > -1:
                        charset = v[charset_pos + 8:]
            content = content.decode(charset)
            # get wordpress page content
            wp_status, wp_content = self.get_wordpress_content(
                environ,
                environ['PATH_INFO'])
            environ[STATUS_KEY] = wp_status
            content = self.replace_relevant_bits(content,
                                                 wp_content,
                                                 status,
                                                 wp_status)
            headers = [(k, v) for k, v in headers \
                       if k != "Content-Length"]
            headers.append(('Content-Length',
                            str(len(content.encode('utf-8')))
                            ))

            if not status.startswith("200"):
                if not wp_status.startswith("404"):
                    status = wp_status
            app_iter = [content]
        start_response(status, headers, exc_info)
        return encode_unicode_app_iter(app_iter,
                                       encoding="utf-8")

    @classmethod
    def replace_relevant_bits(cls,
                              original_content,
                              wp_content,
                              original_status,
                              wp_status):
        '''Replace ```original_content``` with relevant bits of
        ```wp_content```, specifically appending navigation and
        replacing the main content div from CKAN.
        '''
        wp_status_int = int(wp_status[:3])
        original_status_int = int(original_status[:3])
        proxy_host = config.get('wordpresser.proxy_host')
        if wp_status_int == 404 and original_status_int == 404:
            # Allow Error middleware to do its thing
            return original_content
        wp_etree = fromstring(wp_content)
        if original_status_int < 400:
            content_etree = fromstring(original_content)
        elif original_status_int >= 500:
            return original_content
        else:
            basic_template = unicode(render('error_document_template.html'))
            content_etree = fromstring(basic_template)

        # append WP nav onto CKAN nav
        wp_nav = wp_etree.xpath('//div[contains(@class,"menu")]/ul/li')
        if wp_nav:
            try:
                menu = content_etree.xpath('//div[@class="menu"]/ul')[0]
                menu.extend(wp_nav)
            except IndexError:
                # no nav in the page from wordpress
                pass
        # insert WP content into CKAN content area, if required
        if original_status_int >= 400:
            proxy_title = None
            proxy_content = None
            if wp_status_int >= 400:
                # return Wordpress error
                #
                # note that this is never 404, as that is
                # short-circuited above
                wp_error = wp_etree.xpath('//body[@id="error-page"]')
                # set Wordpress' error text to be wrapped in our content div
                proxy_content = wp_error[0]
                proxy_content.tag = "div"
                proxy_content.attrib['id'] = "content"
            else:
                try:
                    proxy_content = wp_etree.xpath(
                        '//div[@id="content"]')[0]
                    proxy_title = wp_etree.xpath('//title')[0]
                except IndexError:
                    # we got something unexpected from Wordpress
                    pass

            if proxy_content is not None:
                orig_content = content_etree.xpath('//div[@id="content"]')[0]
                orig_content.getparent().replace(orig_content,
                                                 proxy_content)
                orig_title = content_etree.xpath('//title')[0]
            if proxy_title is not None:
                orig_title.getparent().replace(orig_title, proxy_title)

        # finally, replace all references to the WP hostname with our
        # own hostname
        content = tostring(content_etree, encoding=unicode)
        return content.replace(proxy_host, "/")

    @classmethod
    @beaker_cache(key='path', expire=60)
    def get_wordpress_content(cls, environ, path):
        # grab the WP page -- we always need it for the nav, at least,
        # and optionally for content when we get a 404 from CKAN.
        from pylons.controllers.util import redirect
        proxy_host = config.get('wordpresser.proxy_host')
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

        if wp_resp.status_int in [301, 302]:
            if proxy_host in wp_resp.location:
                wp_resp.location = wp_resp.location.replace(proxy_host,
                                                            req.host_url + "/")
            redirect(wp_resp.location, code=wp_resp.status_int)
        wp_resp.decode_content()
        # XXX in fact we currently never get content_encoding passed
        # on by the proxy, which is presumably a bug:
        body = wp_resp.body.decode(wp_resp.content_encoding or 'utf-8')
        return (wp_resp.status, body)
