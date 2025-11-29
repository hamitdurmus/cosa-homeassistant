import asyncio
import json
import sys
import os
import importlib.machinery
import types
from unittest.mock import patch

tests_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
package_root = os.path.join(tests_root, 'custom_components')

sys.path.insert(0, tests_root)
sys.modules['custom_components'] = types.ModuleType('custom_components')
sys.modules['custom_components.cosa'] = types.ModuleType('custom_components.cosa')

const_path = os.path.join(package_root, 'cosa', 'const.py')
const_loader = importlib.machinery.SourceFileLoader('custom_components.cosa.const', const_path)
const_loader.load_module()

api_path = os.path.join(package_root, 'cosa', 'api.py')
api_loader = importlib.machinery.SourceFileLoader('custom_components.cosa.api', api_path)
api_loader.load_module()

from custom_components.cosa.api import CosaAPIClient


class SimpleMock:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    async def json(self):
        return self._payload

    async def text(self):
        return json.dumps(self._payload)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def mock_login(url, json_payload=None, headers=None):
    return SimpleMock({"success": True, "data": {"authToken": "SAMPLETOKEN123", "endpoints": [{"id": "end_001"}]}})


def mock_get_endpoint(url, json_payload=None, headers=None):
    return SimpleMock({"endpoint": {"id": "end_001", "temperature": 20.5, "targetTemperatures": {"home": 21}}})


async def run_test():
    client = CosaAPIClient(username="test@example.com", password="testpass")

    def post(url, *args, **kwargs):
        json_payload = kwargs.get('json') or kwargs.get('json_payload')
        if url.endswith('/users/login') or url.endswith('/auth/login'):
            return mock_login(url, json_payload)
        return mock_get_endpoint(url, json_payload)

    def get(url, *args, **kwargs):
        return mock_get_endpoint(url)

    with patch('aiohttp.ClientSession') as MockSession:
        mock_session = MockSession.return_value
        mock_session.post = post
        mock_session.get = get

        await client.login()
        print('Token after login:', client._token)
        eps = await client.list_endpoints()
        print('List endpoints:', eps)
        status = await client.get_endpoint_status('end_001')
        print('Endpoint status:', status)
        await client.close()


if __name__ == '__main__':
    asyncio.run(run_test())
