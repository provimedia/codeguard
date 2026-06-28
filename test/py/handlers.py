"""Event handlers. Most of these are reached only by string, never by a
literal call -- the classic dynamic-dispatch looks-dead pattern in Python."""

REGISTRY = {}


def register(key):
    """Decorator that stores a handler under a string key."""
    def deco(fn):
        REGISTRY[key] = fn
        return fn
    return deco


def handle_payment_succeeded(payload):
    """LIVE_TRAP (py-getattr-dispatch): invoked only via
    getattr(handlers, 'handle_payment_succeeded') in dispatcher.py. There is no
    literal handle_payment_succeeded( ) call anywhere."""
    return {"ok": True, "amount": payload.get("amount", 0)}


def handle_subscription_canceled(payload):
    """LIVE_TRAP (py-getattr-dispatch): reached only via getattr by event name."""
    return {"ok": True, "reason": payload.get("reason", "unknown")}


@register("refund.created")
def on_refund_created(payload):
    """LIVE_TRAP (py-registry-decorator): stored in REGISTRY['refund.created']
    by the decorator above and dispatched purely by that string key."""
    return {"refunded": payload.get("amount", 0)}


def run_registered(key, payload):
    handler = REGISTRY.get(key)
    return handler(payload) if handler else None
