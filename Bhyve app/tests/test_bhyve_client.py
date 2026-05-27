from __future__ import annotations

import unittest
from unittest.mock import Mock

from bhyve_app.bhyve_client import BhyveClient


class BhyveClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_uses_api_key_without_http_request(self) -> None:
        session = Mock()
        client = BhyveClient(None, None, session, api_key="token-123")

        await client.login()

        self.assertEqual(client._token, "token-123")
        session.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()