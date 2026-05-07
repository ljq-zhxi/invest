from __future__ import annotations

from datetime import date

from .models import PositionCycle, Trade


def build_position_cycles(
    trades: list[Trade],
    as_of: date | None = None,
    account_asset: float | None = None,
) -> list[PositionCycle]:
    active_trades = [trade for trade in trades if trade.active_trade]
    active_trades.sort(key=lambda trade: (trade.user_id, trade.account_id, trade.symbol, trade.trade_date, trade.trade_id))
    as_of = as_of or (active_trades[-1].trade_date.date() if active_trades else date.today())
    cycles: list[PositionCycle] = []
    current: dict[tuple[str, str, str], dict[str, object]] = {}

    for trade in active_trades:
        key = (trade.user_id, trade.account_id, trade.symbol)
        state = current.get(key)
        if state is None and trade.side == "SELL":
            continue
        if state is None:
            cycle = PositionCycle(
                cycle_id=f"CYCLE_{len(cycles) + sum(1 for item in current.values() if item) + 1:04d}",
                user_id=trade.user_id,
                account_id=trade.account_id,
                symbol=trade.symbol,
                stock_name=trade.stock_name,
                start_date=trade.trade_date.date(),
                end_date=trade.trade_date.date(),
                status="OPEN",
                first_buy_price=trade.price,
                account_asset_confidence="MEDIUM" if account_asset else "LOW",
            )
            state = {"cycle": cycle, "quantity": 0.0, "cost": 0.0, "realized_cost": 0.0, "sell_amount": 0.0}
            current[key] = state

        cycle = state["cycle"]
        assert isinstance(cycle, PositionCycle)
        quantity = float(state["quantity"])
        cost = float(state["cost"])
        cycle.trades.append(trade)
        cycle.trade_count += 1
        cycle.end_date = trade.trade_date.date()

        if trade.side == "BUY":
            cycle.buy_count += 1
            quantity += trade.quantity
            cost += trade.quantity * trade.price + trade.fee + trade.tax
            cycle.avg_buy_price = cost / quantity if quantity else 0.0
        else:
            cycle.sell_count += 1
            sell_quantity = min(trade.quantity, quantity)
            avg_cost = cost / quantity if quantity else 0.0
            realized = sell_quantity * (trade.price - avg_cost) - trade.fee - trade.tax
            cycle.realized_pnl += realized
            state["sell_amount"] = float(state["sell_amount"]) + sell_quantity * trade.price
            state["realized_cost"] = float(state["realized_cost"]) + sell_quantity * avg_cost
            cost -= sell_quantity * avg_cost
            quantity -= sell_quantity
            cycle.avg_sell_price = float(state["sell_amount"]) / max(1.0, sum(t.quantity for t in cycle.trades if t.side == "SELL"))

        market_value = quantity * trade.price
        cycle.max_position_quantity = max(cycle.max_position_quantity, quantity)
        cycle.max_position_value = max(cycle.max_position_value, market_value)
        if account_asset:
            cycle.max_position_weight = max(cycle.max_position_weight, market_value / account_asset)
        else:
            cycle.max_position_weight = max(cycle.max_position_weight, min(1.0, market_value / max(cycle.max_position_value, 1.0)))
        if quantity > 0 and cost > 0:
            floating = (trade.price - cost / quantity) / (cost / quantity)
            cycle.max_drawdown_pct = min(cycle.max_drawdown_pct, floating)
            cycle.max_profit_pct = max(cycle.max_profit_pct, floating)

        state["quantity"] = quantity
        state["cost"] = max(0.0, cost)
        if quantity <= 0.000001:
            invested = max(float(state["realized_cost"]), 1.0)
            cycle.realized_pnl_pct = cycle.realized_pnl / invested
            cycle.status = "CLOSED"
            cycle.is_current_holding = False
            cycle.hold_days = max(0, (cycle.end_date - cycle.start_date).days)
            cycles.append(cycle)
            current[key] = None

    for state in current.values():
        if not state:
            continue
        cycle = state["cycle"]
        assert isinstance(cycle, PositionCycle)
        cycle.status = "OPEN"
        cycle.is_current_holding = True
        cycle.end_date = as_of
        quantity = float(state["quantity"])
        cost = float(state["cost"])
        last_price = cycle.trades[-1].price
        cycle.unrealized_pnl = quantity * last_price - cost
        cycle.realized_pnl_pct = cycle.realized_pnl / max(cycle.max_position_value, 1.0)
        cycle.hold_days = max(0, (cycle.end_date - cycle.start_date).days)
        cycles.append(cycle)

    return cycles
