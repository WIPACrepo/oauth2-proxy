# oauth2-proxy
Python version of oauth2-proxy

A very limited version of [https://github.com/oauth2-proxy/oauth2-proxy](https://github.com/oauth2-proxy/oauth2-proxy)
written in Python.  Primarily meant for debugging, as it gives much more detailed logging.

## Basic Config

Primary env variables:

* OPENID_CLIENT_ID
* OPENID_CLIENT_SECRET
* OPENID_URL
* OPENID_SCOPES
* OPENID_AUDIENCE

Some host config using env variables:

* FULL_URL - external base url, for redirects to work
* HOST - bind host, set to an empty string for all interfaces
* PORT - bind port

## API Routes

Handles API routes (returning 401 instead of a login redirect) using env variables:

* API_ROUTES - string separated regexp patterns
* API_TOKEN_LEEWAY - extra leeway for validating token expiration

`API_TOKEN_LEEWAY` is usually unnecessary, but may be useful in an environment
with clock skew between the OpenID server and this server.
