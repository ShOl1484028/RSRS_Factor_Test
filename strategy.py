import backtrader as bt
from indicator import RSRSIndicator


class StrategyBase(bt.Strategy):
    def __init__(self):
        self.order=None
        self.signal=None

    def log(self, txt,dt=None):
        """ 日志记录函数 """
        dt=dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        """
        订单状态通知，处理通用逻辑。
        """
        if order.status in [order.Submitted, order.Accepted]:
            self.order = None
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, '
                    f'Comm: {order.executed.comm:.2f}'
                )
            elif order.issell():
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, '
                    f'Comm: {order.executed.comm:.2f}'
                )
            # 订单完成后，重置 self.order
            self.order = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def notify_trade(self, trade):
        """
        交易结果通知。
        """
        if not trade.isclosed:
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def stop(self):
        """ 策略结束时的操作 """
        self.log(f'Ending Value {self.broker.getvalue():.2f}')

class BuyAndHold(StrategyBase):
    def __init__(self):
        super().__init__()
    def next(self):
        if self.order:
            return
        if not self.position:
            self.order=self.order_target_percent(target=0.99)


class RSRSBaseStrategy(StrategyBase):
    params=(('rsrs_period',18),('buy_threshold',1.0),('sell_threshold',0.8))
    def __init__(self):
        super().__init__()
        #取出指标，便于计算和判断
        N=self.params.rsrs_period
        self.ols=RSRSIndicator(self.data,rsrs_period=N)
        self.rsrs_slope=self.ols.slope
        self.signal=self.rsrs_slope
        # self.order 的初始化已经移动到 BaseStrategy 中了
    def next(self):
        if self.order:
            return
        if not self.position:
            if self.rsrs_slope[0]>self.params.buy_threshold:
                self.order=self.order_target_percent(target=0.99)
        else:
            if self.rsrs_slope[0]<self.params.sell_threshold:
                self.order=self.close()

class RSRSRankStrategy(StrategyBase):
    params=(('rsrs_period',18),('rank_period',252),('buy_threshold',0.7),('sell_threshold',0.3))
    def __init__(self):
        super().__init__()
        #取出指标，便于计算和判断
        N=self.params.rsrs_period
        M=self.params.rank_period
        self.ols=RSRSIndicator(self.data,rsrs_period=N)
        self.rsrs_slope=self.ols.slope
        self.rsrs_rank=bt.indicators.PercentRank(self.rsrs_slope,period=M)
        self.signal=self.rsrs_rank
        # self.order 的初始化已经移动到 BaseStrategy 中了
    def next(self):
        if self.order:
            return
        if not self.position:
            if self.rsrs_rank[0]>self.params.buy_threshold:
                self.order=self.order_target_percent(target=0.99)
        else:
            if self.rsrs_rank[0]<self.params.sell_threshold:
                self.order=self.close()

class RSRSZscoreStrategy(StrategyBase):
    params=(('rsrs_period',18),('dist_period',252),('buy_threshold',0.7),('sell_threshold',-0.7))
    def __init__(self):
        super().__init__()
        N=self.params.rsrs_period
        M=self.params.dist_period
        self.ols=RSRSIndicator(self.data,rsrs_period=N,dist_period=M)
        self.rsrs_zscore=self.ols.z_score
        self.signal=self.rsrs_zscore
    def next(self):
        if self.order:
            return
        if not self.position:
            if self.rsrs_zscore[0]>self.params.buy_threshold:
                self.order=self.order_target_percent(target=0.99)
        else:
            if self.rsrs_zscore[0]<self.params.sell_threshold:
                self.order=self.close()

class RSRSRevisedStrategy(StrategyBase):
    params=(('rsrs_period',18),('dist_period',252),('buy_threshold',0.7),('sell_threshold',-0.7))
    def __init__(self):
        super().__init__()
        N=self.params.rsrs_period
        M=self.params.dist_period
        self.ols=RSRSIndicator(self.data,rsrs_period=N,dist_period=M)
        self.revised_rsrs=self.ols.revised_score
        self.signal=self.revised_rsrs
    def next(self):
        if self.order:
            return
        if not self.position:
            if self.revised_rsrs[0]>self.params.buy_threshold:
                self.order=self.order_target_percent(target=0.99)
        else:
            if self.revised_rsrs[0]<self.params.sell_threshold:
                self.order=self.close()

class RSRSRightSkewedStrategy(StrategyBase):
    params=(('rsrs_period',18),('dist_period',252),('buy_threshold',0.7),('sell_threshold',-0.7))
    def __init__(self):
        super().__init__()
        N=self.params.rsrs_period
        M=self.params.dist_period
        self.ols=RSRSIndicator(self.data,rsrs_period=N,dist_period=M)
        self.right_skewed_rsrs=self.ols.right_skewed_score
        self.signal=self.right_skewed_rsrs
    def next(self):
        if self.order:
            return
        if not self.position:
            if self.right_skewed_rsrs[0]>self.params.buy_threshold:
                self.order=self.order_target_percent(target=0.99)
        else:
            if self.right_skewed_rsrs[0]<self.params.sell_threshold:
                self.order=self.close()