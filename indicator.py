import backtrader as bt

class RSRSIndicator(bt.Indicator):
    lines=('slope','intercept','r_squared','z_score', 'revised_score','right_skewed_score',)
    params=(('rsrs_period',18),('dist_period',250),)
    def __init__(self):
        # --- 使用局部变量进行所有中间计算 ---
        N = self.p.rsrs_period
        M = self.p.dist_period
        high=self.data.high
        low =self.data.low
        # 1) β = Cov(high, low, N) / Var(low, N)
        mean_high=bt.indicators.SMA(high,period=N)
        mean_low=bt.indicators.SMA(low,period=N)
        dev_high=high-mean_high
        dev_low=low-mean_low
        std_high = bt.indicators.StdDev(high, period=N)
        std_low = bt.indicators.StdDev(low, period=N)
        # 2) Cov(high, low, N) = E[(high - mean(high, N)) * (low - mean(low, N))]
        cov=bt.indicators.SMA(dev_high*dev_low,period=N)
        # 3) Var(low, N) = E[(low - mean(low, N))²]
        var=bt.indicators.SMA(dev_low*dev_low,period=N)
        # 4) Corr(high, low, N) = Cov(high, low, N) / (std(high, N) * std(low, N))
        #防除零
        eps = 1e-12
        corr=cov/(std_high*std_low+eps)
        slope=cov/(var+eps)
        # 5) α = mean(high, N) - β * mean(low, N)
        intercept=mean_high-slope*mean_low
        # 6) R² = Corr(high, low, N)²
        r_squared=corr*corr
        # 7) z-score = (β - mean(β, M)) / std(β, M)
        beta_mean=bt.indicators.SMA(slope,period=M)
        beta_std=bt.indicators.StdDev(slope,period=M)
        z_score=(slope-beta_mean)/(beta_std + eps)
        revised_score=z_score*r_squared
        right_skewed_score=z_score*r_squared*slope
        # --- 最后一步：将所有最终结果赋给 self.lines ---
        self.l.slope = slope
        self.l.intercept = intercept
        self.l.r_squared = r_squared
        self.l.z_score = z_score
        self.l.revised_score=revised_score
        self.l.right_skewed_score=right_skewed_score
        self.addminperiod(max(N, M))
