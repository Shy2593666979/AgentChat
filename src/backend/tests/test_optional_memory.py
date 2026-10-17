import unittest
from unittest.mock import AsyncMock

from agentchat.services.memory.optional import (
    search_optional_memory,
    store_optional_memory,
)


class OptionalMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_user_scope_is_preserved_for_mars(self):
        client = AsyncMock()
        client.search.return_value = {
            "results": [],
        }
        self.assertEqual(await search_optional_memory(client, query="hello", user_id="user"), ("", True))
        client.search.assert_awaited_once_with(query="hello", user_id="user")
        self.assertTrue(await store_optional_memory(client, messages=[], user_id="user"))
        client.add.assert_awaited_once_with(messages=[], user_id="user")

    async def test_search_failure_does_not_abort_chat(self):
        client = AsyncMock()
        client.search.side_effect = RuntimeError('unavailable')
        self.assertEqual(await search_optional_memory(client, query='hello', run_id='conversation'), (None, False))

    async def test_search_preserves_successful_results(self):
        client = AsyncMock()
        client.search.return_value = {
            'results': [
                {
                    'memory': 'first',
                },
                {
                    'memory': 'second',
                },
            ],
        }
        self.assertEqual(await search_optional_memory(client, query='hello', run_id='conversation'), ('first\nsecond', True))

    async def test_write_failure_does_not_abort_history_saving(self):
        client = AsyncMock()
        client.add.side_effect = RuntimeError('unavailable')
        self.assertFalse(await store_optional_memory(client, messages=[], run_id='conversation'))

    async def test_write_success_is_reported(self):
        client = AsyncMock()
        self.assertTrue(await store_optional_memory(client, messages=[], run_id='conversation'))
        client.add.assert_awaited_once_with(messages=[], run_id='conversation')
