from flask import request, g
from main import env_test, app, nycu_oauth, authService, dnsService
import config

@app.before_request
def before_request():

    g.user = authService.authenticate_token(request.headers.get('Authorization'))

@app.route("/oauth/<string:code>", methods = ['GET'])
def get_token(code):

    token = nycu_oauth.get_token(code)
    if token:
        return {'token': authService.issue_token(nycu_oauth.get_profile(token))}
    else:
        return {'message': "Invalid code."}, 401

@app.route("/test_auth/", methods = ['GET'])
def get_token_for_test():

    if env_test:
        return {'token': authService.issue_token(config.TEST_PROFILE)}
    else:
        return {'message': "It is not currently running on testing mode."}, 401

@app.route("/whoami/", methods = ['GET'])
def whoami():
    if g.user:
        data = {}
        data['uid'] = g.user['uid']
        data['email'] = g.user['email']
        data['domains'] = dnsService.list_domains_by_user(g.user['uid'])
        return data
    return {"message": "Unauth."}, 401
