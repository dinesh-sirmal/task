import json

import app.rag_engine as rag_engine
import app.logger as app_logger


def test_logger_emits_required_fields(monkeypatch):
    captured = {}

    def fake_info(msg):
        # store last logged JSON
        try:
            captured['msg'] = json.loads(msg)
        except Exception:
            captured['msg'] = None

    monkeypatch.setattr(app_logger, 'logger', type('L', (), {'info': staticmethod(fake_info)}))

    # Mock retrieval: return a clear match
    monkeypatch.setattr(rag_engine.vector_store, 'query', lambda q: [{
        'text': 'auth info', 'source': '02_authentication.md', 'chunk_id': 0, 'distance': 0.1
    }])

    # Mock LLM generation
    monkeypatch.setattr(rag_engine, 'generate', lambda prompt: ("OK", 12))

    res = rag_engine.answer_query('How does authentication work?')

    assert 'msg' in captured and isinstance(captured['msg'], dict)
    msg = captured['msg']

    # Check required fields
    for key in ['retrieval_time_ms', 'generation_time_ms', 'total_time_ms', 'approx_tokens_used', 'num_sources', 'best_retrieval_score', 'configured_threshold', 'used_fallback']:
        assert key in msg
    assert msg['used_fallback'] is False
