import httplib
import re

from ckan.config.middleware import make_app
from paste.deploy import appconfig
import paste.fixture
from ckan.tests import conf_dir, url_for, CreateTestData

from ckanext.wordpresser import WordpresserMiddleware as middleware
from mockwordpress import runmockserver


class TestWordpresser:
    @classmethod
    def setup_class(cls):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'wordpresser'
        config.local_conf['wordpresser.proxy_host'] \
                              = 'http://localhost:6969/'
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)
        CreateTestData.create()
        runmockserver()

    @classmethod
    def teardown_class(cls):
        CreateTestData.delete()
        conn = httplib.HTTPConnection("localhost:%d" % 6969)
        conn.request("QUIT", "/")
        conn.getresponse()

    def test_head_ok(self):
        response = self.app._gen_request('HEAD', '/about')
        assert 'OK' in response.full_status, response

    def test_post_ok(self):
        url = url_for('about')
        response = self.app._gen_request('POST', url)
        assert 'OK' in response.full_status, response

    def test_200_transcode(self):
        response = self.app._gen_request('GET', '/about')
        assert 'wp-nav-1' in response.body
        assert 'Wobsnasm' not in response.body

    def test_500_in_ckan(self):
        environ = {'PATH_INFO': 'about',
                   'REQUEST_METHOD': 'GET'}
        wp_status, wp_content = middleware.get_wordpress_content(
            environ,
            'about')
        repl = middleware.replace_relevant_bits("some_error",
                                                wp_content,
                                                "500 oops",
                                                wp_status)
        assert repl == "some_error", repl

    def test_200_but_500_in_wp_transcode(self):
        url = url_for('license')
        response = self.app._gen_request('GET', url)
        assert 'wp-nav-1' not in response.body
        assert 'someerror' not in response.body

    def test_404_but_200_in_wp_transcode(self):
        url = url_for('/exists_in_wordpress')
        response = self.app._gen_request('GET', url)
        assert 'wp-nav-1' in response.body
        assert 'Wobsnasm' in response.body

    def test_404_but_500_in_wp_transcode(self):
        url = url_for('/error_in_wordpress')
        response = self.app._gen_request('GET', url, status=500)
        assert 'wp-nav-1' in response.body
        assert 'whoopsy' in response.body

    def test_404_in_both_places(self):
        response = self.app._gen_request('GET', '/404', status=404)
        assert 'blah' not in response.body
        titles = re.findall(r"<title>", response.body)
        # there was an error to do with Error middleware that meant we
        # got duplicate page content
        assert len(titles) == 1, len(titles)

    def test_utf8_from_wp(self):
        response = self.app._gen_request('GET', '/utf8_in_wordpress')
        assert '\xc3\xbe' in response.body

    def test_bad_wordpress_markup(self):
        response = self.app._gen_request('GET', '/notworking')
        assert "empty" not in response.body

    def test_wordpress_redirect(self):
        response = self.app._gen_request('GET', '/redirect')
        assert 'wp-nav-1' in response.body
        assert 'Wobsnasm' in response.body

    def test_no_nav_in_ckan(self):
        environ = {'PATH_INFO': 'about',
                   'REQUEST_METHOD': 'GET'}
        wp_status, wp_content = middleware.get_wordpress_content(
            environ,
            'about')
        repl = middleware.replace_relevant_bits("not much",
                                                wp_content,
                                                "200 OK",
                                                wp_status)
        assert repl == "<p>not much</p>", repl

       
