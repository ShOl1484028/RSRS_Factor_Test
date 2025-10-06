import backtrader as bt
import pandas as pd
import numpy as np
import scipy.stats

class ICAnalyzer(bt.Analyzer):
    """
    计算信号与未来N期收益的IC（Information Coefficient）
    - 使用 Spearman 秩相关系数
    """
    params = (
        ('period', 10),      # 默认计算未来10期的收益
        ('min_samples', 15), # 设定最小IC样本门槛，因为太少IC分析会无意义
    )

    def __init__(self):
        # 步骤1: 在 __init__ 中，直接创建一个收益率指标。
        # 我们需要的是未来收益，但这里先计算每期的收益率。
        # 注意：这里的 period=1 是为了计算单期收益率。
        self.returns_indicator = bt.indicators.PercentChange(self.data, period=1)
        # 注意：这里不再需要 self.signals 和 self.returns 列表了！

    def start(self):
        # 检查策略是否暴露了 signal 指标
        if self.strategy.signal is None:
            raise AttributeError("策略对象必须有一个 'signal' 属性用于IC分析。")

    def next(self):
        pass

    def get_analysis(self):
        # 步骤 0: 从 backtrader lines 获取原始数据
        signal_series = pd.Series(self.strategy.signal.lines[0].array, name='signal')
        return_series = pd.Series(self.returns_indicator.lines[0].array, name='return')

        # 步骤 1: 先将原始的 signal 和 return 合并
        df = pd.concat([signal_series, return_series], axis=1)

        # 步骤 2: 在合并后的 DataFrame 内部创建 'future_return' 列
        df['future_return'] = df['return'].shift(-self.p.period)

        # 步骤 3: 现在安全地删除任何包含 NaN 的行
        df.dropna(inplace=True)   
        # 步骤 4: 计算 IC
        if len(df) < self.p.min_samples:
            ic_corr = float('nan')
            print(f"警告: 有效样本量 {len(df)} 小于最小要求 {self.p.min_samples}，IC无法计算。")
        else:
            # 关键：使用清洗和对齐后的 'signal' 和 'future_return' 列
            ic_corr, _ = scipy.stats.spearmanr(df['signal'], df['future_return'])
            
        return {f'ic_spearman_p{self.p.period}': ic_corr}

