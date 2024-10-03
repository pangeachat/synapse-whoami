from synapse.api.errors import AuthError
from synapse.http import server
from synapse.http.server import respond_with_json
from synapse.http.site import SynapseRequest
from synapse.module_api import ModuleApi
from twisted.internet import defer
from twisted.web.resource import Resource


class WhoAmI(Resource):
    isLeaf = True

    def __init__(self, module_api: ModuleApi):
        super().__init__()
        self.module_api = module_api
        self.auth = module_api._hs.get_auth()

    def render_GET(self, request: SynapseRequest):
        defer.ensureDeferred(self._async_render_GET(request))
        return server.NOT_DONE_YET

    async def _async_render_GET(self, request: SynapseRequest):
        try:
            # Authenticate the request using the access token
            requester = await self.auth.get_user_by_req(request)
            user_id = requester.user.to_string()

            respond_with_json(request, 200, {"user_id": user_id}, send_cors=True)
        except AuthError:
            respond_with_json(
                request, 401, {"error": "Invalid access token"}, send_cors=True
            )
        except Exception as e:
            respond_with_json(request, 500, {"error": str(e)}, send_cors=True)
