"""Test environment setup — loaded before any test module is collected.

Ensures src/services/llm.py can import without a real OPENAI_API_KEY
(CI has no .env file). All OpenAI HTTP calls are mocked in test_llm_check
via unittest.mock.patch — this placeholder is never sent over the wire.

setdefault preserves any real key from .env for local integration runs.
"""

import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-mock-no-real-calls")
