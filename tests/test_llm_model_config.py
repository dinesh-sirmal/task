from app.config import GEMINI_MODEL


def test_default_gemini_model_is_supported_by_current_api():
    assert GEMINI_MODEL in {
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-2.5-flash-lite",
    }
