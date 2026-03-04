# TODO

Security and code quality fixes identified during review.

---

## [MEDIUM] Ticker input injected into HTML without sanitization

**Files:**
- `src/app.py` ~line 733
- `src/ui_components.py` ~line 635

**Problem:**
The ticker string from user input is embedded directly into HTML strings rendered via `st.markdown(..., unsafe_allow_html=True)`. The only preprocessing is `.strip().upper()`, which does not prevent XSS. A payload like `<img src=x onerror=alert(1)>` survives uppercasing.

**Fix:**
1. In `app.py`, import and call `validate_ticker()` from `utils/validators.py` **before** storing the ticker in `st.session_state`. Reject input that does not match `^[\^]?[A-Z]{1,5}$`.
2. Also apply `html.escape()` on the ticker before embedding it in any f-string that goes into `st.markdown(..., unsafe_allow_html=True)`.

```python
# app.py — example
import html
from utils.validators import validate_ticker

ticker_input = ticker_input.strip().upper()
if not validate_ticker(ticker_input):
    st.error("Invalid ticker symbol.")
    st.stop()

# when embedding in HTML
safe_ticker = html.escape(ticker_input)
```

---

## [MEDIUM] LLM output injected into HTML without escaping

**File:** `src/app.py` ~line 736

**Problem:**
The raw string returned by the local Ollama model (`insight_text`) is interpolated directly into an HTML block and passed to `st.markdown(..., unsafe_allow_html=True)` with no sanitization. A prompt injection that coerces the model to output `<script>` or `<img onerror=...>` tags would execute in the browser.

**Fix:**
Apply `html.escape()` to `insight_text` before embedding it in the HTML string. The existing `fix_text_spacing()` call in `src/llm_insights.py` should happen first (to clean up spacing), then escape for HTML.

```python
# app.py — example
import html

safe_insight = html.escape(insight_text)
st.markdown(
    f'<div class="ai-analysis-content">{safe_insight}</div>',
    unsafe_allow_html=True,
)
```

Note: `html.escape()` converts `<`, `>`, `&`, `"`, `'` to their HTML entities, which preserves the text visually while preventing execution.

---

## [LOW] `validate_ticker()` is defined but never used in the application

**File:** `utils/validators.py` — function `validate_ticker()`

**Problem:**
The function is well-implemented and fully tested, but it is never imported or called in `src/app.py` or `src/data_fetcher.py`. The raw (only uppercased) ticker is passed directly to `yf.Ticker(ticker)` and embedded in HTML.

**Fix:**
This is resolved by the fix described in the first item above. Verify after that change that `validate_ticker` is imported and called in `app.py` before any use of the ticker value.

---

## [LOW] Silent broad exception suppression

**Files:** `src/indicators.py`, `src/data_fetcher.py`, `src/llm_insights.py`, `src/app.py`

**Problem:**
Multiple `except Exception: return None` and `except Exception: pass` blocks swallow errors silently. This makes failures invisible and can mask security-relevant conditions (e.g., a failed data integrity check returning `None` that the caller silently ignores).

**Fix:**
Replace bare `except Exception: pass/return None` with at minimum a logger warning. Each module already has or can create a logger via `utils/logger.py`.

```python
# before
except Exception:
    return None

# after
except Exception as e:
    logger.warning("Failed to compute X: %s", e)
    return None
```

Do a project-wide search for `except Exception:` followed by `return None` or `pass` and add logging to each one.
