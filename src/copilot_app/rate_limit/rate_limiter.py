from __future__ import annotations

import logging
from typing import Dict

from . import strategies

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, strategy=None) -> None:
        # strategy is a prototype; per-identifier clones are created
        self._strategy_proto = strategy or strategies.TokenBucketStrategy()
        self._per_id: Dict[str, object] = {}

    def set_strategy(self, strategy) -> None:
        self._strategy_proto = strategy

    def get_strategy(self):
        return self._strategy_proto

    def allow_request(self, identifier: str) -> bool:
        if identifier not in self._per_id:
            try:
                self._per_id[identifier] = self._strategy_proto.clone()
            except Exception:
                logger.exception("Failed cloning strategy for %s", identifier)
                self._per_id[identifier] = self._strategy_proto

        strat = self._per_id[identifier]
        # strategy may expose consume() or allow()
        try:
            if hasattr(strat, "consume"):
                allowed = strat.consume()
            elif hasattr(strat, "allow"):
                allowed = strat.allow()
            else:
                logger.error("Strategy for %s has no consume/allow method", identifier)
                return True
            logger.debug("RateLimiter allow_request %s -> %s", identifier, allowed)
            return bool(allowed)
        except Exception:
            logger.exception("Error evaluating rate limit for %s", identifier)
            return False


# module-level default
global_rate_limiter: RateLimiter | None = None
