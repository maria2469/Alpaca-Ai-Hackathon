"""Hand-written duck-typed fakes for the Alpaca clients. No network anywhere."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from alpaca.trading.enums import (
    AssetClass,
    OrderClass,
    OrderSide,
    OrderStatus,
    PositionIntent,
    PositionSide,
    QueryOrderStatus,
)

NOW = datetime(2026, 8, 31, 15, 0, tzinfo=timezone.utc)
TODAY = NOW.date()


def fake_clock(is_open: bool = True, server_time: datetime = NOW) -> SimpleNamespace:
    return SimpleNamespace(
        timestamp=server_time, is_open=is_open, next_close=server_time + timedelta(hours=3)
    )


def fake_account(equity: float | None = 100_000.0, level: int = 3) -> SimpleNamespace:
    return SimpleNamespace(equity=equity, options_trading_level=level)


def fake_position(
    symbol: str,
    qty: int,
    avg_entry_price: float,
    side: str = "long",
    unrealized_pl: float | None = None,
    current_price: float | None = None,
) -> SimpleNamespace:
    # Real SDK enums, matching what the live client returns: str() of them is
    # "AssetClass.US_OPTION" / "PositionSide.SHORT", which once hid all positions.
    return SimpleNamespace(
        symbol=symbol,
        qty=str(abs(qty)),
        side=PositionSide.SHORT if "short" in side else PositionSide.LONG,
        avg_entry_price=str(avg_entry_price),
        asset_class=AssetClass.US_OPTION,
        unrealized_pl=None if unrealized_pl is None else str(unrealized_pl),
        current_price=None if current_price is None else str(current_price),
    )


def fake_mleg_fill(
    client_order_id: str,
    legs: list[tuple[str, str, str, float]],
    qty: int,
    filled_at: datetime = NOW,
    status: OrderStatus = OrderStatus.FILLED,
    order_class: OrderClass = OrderClass.MLEG,
) -> SimpleNamespace:
    """A closed MLEG order as the SDK returns it with nested=True.

    legs: (symbol, "buy"|"sell", "buy_to_open"|..., filled_avg_price).
    The parent's filled_avg_price is the net (+buy −sell), like the real API.
    """
    leg_models = [
        SimpleNamespace(
            symbol=symbol,
            side=OrderSide(side),
            position_intent=PositionIntent(intent),
            filled_avg_price=str(price),
            filled_qty=str(qty),
            status=status,
        )
        for symbol, side, intent, price in legs
    ]
    net = sum(price if side == "buy" else -price for _, side, _, price in legs)
    return SimpleNamespace(
        id=f"id-{client_order_id}",
        client_order_id=client_order_id,
        order_class=order_class,
        status=status,
        qty=str(qty),
        filled_qty=str(qty),
        filled_avg_price=str(round(net, 4)),
        filled_at=filled_at,
        legs=leg_models,
    )


def fake_contract(symbol: str, strike: float, expiration: date, open_interest: int = 500) -> SimpleNamespace:
    return SimpleNamespace(
        symbol=symbol,
        strike_price=str(strike),
        expiration_date=expiration,
        open_interest=str(open_interest),
    )


def fake_snapshot(
    bid: float | None,
    ask: float | None,
    iv: float | None = 0.20,
    stamp: datetime = NOW,
) -> SimpleNamespace:
    quote = None
    if bid is not None or ask is not None:
        quote = SimpleNamespace(bid_price=bid, ask_price=ask, timestamp=stamp)
    return SimpleNamespace(latest_quote=quote, implied_volatility=iv)


class FakeTradingClient:
    def __init__(
        self,
        *,
        account=None,
        clock=None,
        positions=(),
        orders=(),
        contracts=(),
        submit_error: Exception | None = None,
        order_statuses: dict | None = None,
        cancel_error: Exception | None = None,
        closed_orders=(),
    ):
        self.account = account or fake_account()
        self.clock = clock or fake_clock()
        self.positions = list(positions)
        self.orders = list(orders)
        self.closed_orders = list(closed_orders)
        self.contracts = list(contracts)
        self.submit_error = submit_error
        self.submitted: list = []
        self.order_statuses = dict(order_statuses or {})
        self.cancel_error = cancel_error
        self.canceled: list = []

    def get_clock(self):
        return self.clock

    def get_account(self):
        return self.account

    def get_all_positions(self):
        return self.positions

    def get_orders(self, request):
        if getattr(request, "status", None) == QueryOrderStatus.CLOSED:
            return self.closed_orders
        return self.orders

    def get_option_contracts(self, request):
        root = getattr(request, "root_symbol", None)  # the real API scopes by underlying
        contracts = [c for c in self.contracts if not root or str(c.symbol).startswith(root)]
        return SimpleNamespace(option_contracts=contracts, next_page_token=None)

    def submit_order(self, request):
        if self.submit_error is not None:
            raise self.submit_error
        self.submitted.append(request)
        return SimpleNamespace(id="order-1", status="accepted")

    def get_order_by_id(self, order_id):
        if order_id not in self.order_statuses:
            raise KeyError(order_id)
        return SimpleNamespace(id=order_id, status=self.order_statuses[order_id])

    def cancel_order_by_id(self, order_id):
        if self.cancel_error is not None:
            raise self.cancel_error
        self.canceled.append(order_id)


def fake_bar(stamp: datetime, open_: float, high: float, low: float, close: float,
             volume: float = 1000.0) -> SimpleNamespace:
    return SimpleNamespace(timestamp=stamp, open=open_, high=high, low=low,
                           close=close, volume=volume)


def quiet_bars(count: int = 60, *, end: datetime | None = None, bar_seconds: int = 900,
               base: float = 100.0) -> list[SimpleNamespace]:
    """Gently drifting completed bars: ATR ~1, tiny bodies/gaps, no events.
    Adjusted to ensure RSI stays in safe range (30-70) for testing."""
    end = end if end is not None else NOW - timedelta(seconds=bar_seconds)
    bars = []
    for i in range(count):
        stamp = end - timedelta(seconds=bar_seconds * (count - 1 - i))
        # Create very small oscillating price to keep RSI in safe range (around 50)
        close = base + 0.05 * ((i % 10) - 5)  # Very small oscillation around base
        bars.append(fake_bar(stamp, close - 0.02, close + 0.5, close - 0.5, close))
    return bars


def breakout_bars(count: int = 60, direction: str = "up", **kwargs) -> list[SimpleNamespace]:
    """quiet_bars but the last bar has a large body to trigger breakout event:
    breakout_up, or breakout_down with direction="down".
    Uses large gap/body to ensure events fire despite RSI constraints."""
    bars = quiet_bars(count, **kwargs)
    prev_close = bars[-2].close
    # Use a very large move to exceed both ATR threshold and overcome RSI constraints
    # With ATR ~1.0, need > 2.0 for event
    body = 4.0 if direction == "up" else -4.0
    close = prev_close + body
    bars[-1] = fake_bar(bars[-1].timestamp, prev_close, max(prev_close, close) + 0.2,
                        min(prev_close, close) - 0.2, close)
    return bars


class FakeStockDataClient:
    def __init__(self, bars_by_symbol=None, quotes_by_symbol=None, bars_error=None):
        self.bars_by_symbol = bars_by_symbol or {}
        self.quotes_by_symbol = quotes_by_symbol or {}
        self.bars_error = bars_error

    def get_stock_bars(self, request):
        if self.bars_error is not None:
            raise self.bars_error
        return SimpleNamespace(data=self.bars_by_symbol)

    def get_stock_latest_quote(self, request):
        # (bid, ask) tuples are fresh as of NOW; a 3-tuple (bid, ask, stamp) sets the quote time.
        return {
            symbol: SimpleNamespace(
                bid_price=q[0], ask_price=q[1], timestamp=q[2] if len(q) > 2 else NOW
            )
            for symbol, q in self.quotes_by_symbol.items()
        }


class FakeOptionDataClient:
    """Serves snapshot dicts; pass a list to serve different answers per call."""

    def __init__(self, snapshots):
        self.queue = snapshots if isinstance(snapshots, list) else [snapshots]
        self.calls = 0

    def get_option_snapshot(self, request):
        snapshots = self.queue[min(self.calls, len(self.queue) - 1)]
        self.calls += 1
        return {s: snapshots[s] for s in request.symbol_or_symbols if s in snapshots}
