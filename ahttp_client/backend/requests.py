import requests

from .base import SyncBackendSession


class RequestSession(requests.Session, SyncBackendSession):
    def wrapped_close(self):
        self.close()

    def wrapped_request(self, method: str, path: str, **kwargs):
        return self.request(method, path, **kwargs)

    def wrapped_get(self, path: str, **kwargs):
        return self.get(path, **kwargs)

    def wrapped_post(self, path: str, **kwargs):
        return self.post(path, **kwargs)

    def wrapped_options(self, path: str, **kwargs):
        return self.options(path, **kwargs)

    def wrapped_delete(self, path: str, **kwargs):
        return self.delete(path, **kwargs)

    def wrapped_patch(self, path: str, **kwargs):
        return self.patch(path, **kwargs)

    def wrapped_put(self, path: str, **kwargs):
        return self.put(path, **kwargs)
