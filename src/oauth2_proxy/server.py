import logging
import os
import re

from tornado.web import RequestHandler, HTTPError
from rest_tools.server import (
    OpenIDLoginHandler,
    OpenIDCookieHandlerMixin,
    RestHandler,
    RestHandlerSetup,
    RestServer,
)

from . import __version__ as version
from .config import ENV


logger = logging.getLogger('server')


API_RE = [
    re.compile(route)
    for route in ENV.API_ROUTES.split()
    if route
]


class Error(RequestHandler):
    def prepare(self):
        raise HTTPError(404, 'invalid route')


class BaseHandler(RestHandler):
    def write_error(self, *args, **kwargs):
        RequestHandler.write_error(self, *args, **kwargs)


class Auth(BaseHandler):
    def get(self):
        logging.debug('request headers: %r', dict(self.request.headers))

        path = self.request.headers.get('X-Auth-Request-Redirect', '')
        logging.info('original path: %s', path)
        if API_RE and path and any(r.match(path) for r in API_RE):
            if not self.current_user:
                logging.warning('API: Not authenticated')
                raise HTTPError(401, 'not authorized')

        elif not OpenIDCookieHandlerMixin.get_current_user(self):
            logging.warning('Not authenticated')
            raise HTTPError(401, 'not authorized')

        self.set_status(204)


class Health(BaseHandler):
    async def get(self):
        ret = {}
        try:
            self.auth.provider_info['authorization_endpoint']
            ret['openid_info'] = True
        except Exception:
            self.set_status(500)
            ret['openid_info'] = False
        self.write(ret)


class Server:
    def __init__(self):
        static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

        handler_config = {
            'debug': ENV.DEBUG,
            'server_header': f'OAuth2 Proxy {version}',
        }

        if ENV.CI_TEST:
            auth = {
                'secret': 'secret'
            }
        else:
            auth = {
                'openid_url': ENV.OPENID_URL,
                'issuers': ENV.OPENID_URL,
                'audience': ENV.OPENID_AUDIENCE,
                'leeway': ENV.API_TOKEN_LEEWAY,
            }
        handler_config['auth'] = auth

        kwargs = RestHandlerSetup(handler_config)

        login_kwargs = kwargs.copy()
        login_kwargs.update({
            'oauth_client_id': ENV.OPENID_CLIENT_ID,
            'oauth_client_secret': ENV.OPENID_CLIENT_SECRET,
            'oauth_client_scope': ENV.OPENID_SCOPES,
        })

        server = RestServer(
            static_path=static_path,
            template_path=template_path,
            cookie_secret=ENV.COOKIE_SECRET,
            login_url=f'{ENV.FULL_URL}/oauth2/start',
            debug=ENV.DEBUG,
        )

        server.add_route('/oauth2/auth', Auth, kwargs)
        server.add_route('/oauth2/start', OpenIDLoginHandler, login_kwargs)
        server.add_route('/healthz', Health, kwargs)

        server.startup(address=ENV.HOST, port=ENV.PORT)

        self.server = server

    async def start(self):
        pass

    async def stop(self):
        await self.server.stop()
