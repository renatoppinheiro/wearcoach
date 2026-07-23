# Known Concerns & Technical Debt

**Last Updated:** 2026-07-22

## Technical Debt & Architectural Fragility

### 1. Unofficial Garmin Connect Integration (`coach/garmin.py`)
- **Issue:** Uses `garminconnect`, an unofficial reverse-engineered Python wrapper for Garmin Connect.
- **Risk:** Garmin API endpoint changes or auth protocol updates may break integration unexpectedly without official deprecation notices.
- **Mitigation:** Comprehensive unit tests in `tests/test_garmin.py` catch payload/auth structure shifts early.

### 2. Hardcoded OAuth Loopback Port (`coach/oauth_loopback.py`)
- **Issue:** OAuth redirect server defaults to port `8734` (`http://localhost:8734/callback`).
- **Risk:** Port conflicts if port 8734 is already bound by another background application on the host machine.
- **Improvement:** Support fallback port attempt or configurable port environment variable.

### 3. Mutual Exclusivity of Wellness Sources (`main.py:_fetch_all`)
- **Issue:** If both Oura Ring and Garmin Connect are authorized, `wearcoach` defaults exclusively to Oura (`if oura.is_connected(): ... elif garmin.is_connected(): ...`).
- **Impact:** Dual-device users cannot merge Oura readiness/sleep data with Garmin ACWR/body battery in a single snapshot.
- **Improvement:** Allow merging multi-provider wellness metrics into unified snapshot schema.

---

## Security & Credential Considerations

### Plaintext Garmin Credentials in `.env`
- **Context:** `garminconnect` requires raw email and password to authenticate.
- **Risk:** Stored in local `.env` file in plaintext.
- **Mitigation:** Ensure `.env` remains strictly gitignored and directory permissions are restricted to local user.

---

## Operational & Robustness Enhancements

### Network Retry & Rate Limiting
- **Issue:** Direct `requests.get` / `requests.post` calls in `strava.py` and `oura.py` lack explicit exponential backoff/retry mechanisms for HTTP 429 (rate limited) or transient HTTP 5xx server errors.
- **Improvement:** Add `urllib3.util.Retry` session adapter or retry helper wrapper for outgoing HTTP requests.
