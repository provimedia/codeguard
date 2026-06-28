"""Routes incoming events to handlers by name. The handler functions are never
named literally here -- they are resolved from the event string at runtime."""

import handlers


def dispatch(event: str, payload: dict):
    # getattr-by-name: e.g. event="payment_succeeded" -> handle_payment_succeeded.
    func = getattr(handlers, f"handle_{event}", None)
    if func is None:
        return None
    return func(payload)


def dispatch_registered(key: str, payload: dict):
    # registry-by-string-key: e.g. "refund.created" -> on_refund_created.
    return handlers.run_registered(key, payload)
