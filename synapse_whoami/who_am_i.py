from twisted.web import resource, server
from twisted.internet import defer
import json
from synapse.module_api import ModuleApi
from synapse.api.errors import AuthError


class WhoAmIResource(resource.Resource):
    def __init__(self, api: ModuleApi):
        super().__init__()
        self.isLeaf = True
        self.api = api

    def render_GET(self, request):
        d = self._get_user_info(request)

        def on_success(result):
            user = result.get("user")
            response_data = {"user": user}
            self._respond(request, 200, response_data)

        def on_failure(failure):
            print(f"Error: {failure}")
            response_data = {"user": None}
            self._respond(request, 401, response_data)

        d.addCallback(on_success)
        d.addErrback(on_failure)

        return server.NOT_DONE_YET

    @defer.inlineCallbacks
    def _get_user_info(self, request):
        access_token = self._get_access_token(request)
        print(f"Access token: {access_token}")
        if access_token:
            try:
                user_info = yield self.api.get_user_by_req(request)
                print(f"User info: {user_info}")
                defer.returnValue({"user": user_info.user})
            except AuthError as e:
                print(f"Invalid access token: {e}")
                raise e
        else:
            defer.returnValue({"user": None})

    def _get_access_token(self, request):
        query_params = request.args
        if b"access_token" in query_params:
            return query_params[b"access_token"][0].decode("utf-8")
        else:
            auth_header = request.getHeader("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                return auth_header.split(" ")[1]

    def _respond(self, request, code, response_data):
        request.setResponseCode(code)
        request.setHeader(b"content-type", b"application/json")
        response = json.dumps(response_data)
        request.write(response.encode("utf-8"))
        request.finish()
