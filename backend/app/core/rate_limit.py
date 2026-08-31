from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory storage — fine for a single-process deployment. A multi-instance
# deployment needs a shared backend (Redis) or this only rate-limits per
# instance, not per account overall.
limiter = Limiter(key_func=get_remote_address)
