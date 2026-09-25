class TransactionCostModel:
    def __init__(self, cost_pct=0.001, slippage_pct=0.0005):
        self.cost_pct = cost_pct
        self.slippage_pct = slippage_pct
    def calculate(self, trade_value, position_change):
        cost = abs(position_change) * self.cost_pct * trade_value
        slip = abs(position_change) * self.slippage_pct * trade_value
        return {'transaction_cost': cost, 'slippage': slip, 'total': cost + slip}
