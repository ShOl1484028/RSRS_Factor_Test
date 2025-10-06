## RSRS 策略组件说明

### 目录结构
- `RSRS_test.py`: 批量回测入口，循环运行多种 RSRS 策略并输出汇总表
- `strategy.py`: 各策略类与基础策略基类（含下单、日志、公共方法）
- `indicator.py`: RSRS 指标实现（β、r²、z-score、修正/右偏）
- `analyzer.py`: 自定义 IC 分析器（IC/IC_IR 可扩展）
- `report.py`: 汇总回测结果并生成可读的对比表
- `data_loader.py`: 数据加载与 `PandasData` 封装（若需要扩展数据来源）

### 依赖
- Python 3.8+
- backtrader
- pandas, numpy, scipy, matplotlib

安装示例：
```bash
pip install backtrader pandas numpy scipy matplotlib
```

### 快速开始
1) 准备数据（CSV，含列：`open, high, low, close, volume`；索引 `datetime`）
2) 运行批量回测：
```bash
python RSRS_test.py
```
控制台将打印：
- 每个策略的交易明细（在策略名标题下）
- 最后输出“策略对比汇总表”包含：总收益、年化、最大回撤、夏普、胜率、盈亏比、IC 等

### 核心指标（indicator.py）
- RSRS β：`β = Cov(high, low, N) / Var(low, N)`
- r²：`r² = Corr(high, low, N)^2`
- z-score：`(β - SMA(β, M)) / Std(β, M)`
- 修正分数（revised）：`z_score * r_squared`
- 右偏分数（right_skewed）：`z_score * r_squared * slope`

实现要点：
- 使用 backtrader 的 `lines` 组合在 `__init__` 中声明计算图，历史会在预加载阶段预计算
- 对分母统一加 `eps` 防除零；必要处清洗 inf/NaN

### 策略（strategy.py）
- `StrategyBase`: 通用基类，封装日志、下单、交易通知；`self.signal` 暴露给分析器
- 已内置的示例策略：
  - `RSRSBaseStrategy`：用 β 与阈值交易
  - `RSRSRankStrategy`：用 `PercentRank(β)` 的分位点交易
  - `RSRSZscoreStrategy`：用 z-score 交易
  - `RSRSRevisedStrategy`：用 `z_score * r²` 交易
  - `RSRSRightSkewedStrategy`：用 `z_score * r² * slope` 交易

注意：各策略在 `__init__` 中将一条 `lines` 赋给 `self.signal`，供 IC 分析器读取。

### 分析器（analyzer.py）
- `ICAnalyzer`：计算因子与未来 N 期累计收益的 Spearman IC
  - 从策略 `self.signal`（必须是 `lines`）取因子序列
  - 从 `self.data.close` 计算未来 `period` 期累计收益 `(close[t+N]/close[t]-1)`
  - 对齐、清洗（含 inf→NaN），样本/方差门槛后计算 IC

示例添加：
```python
cerebro.addanalyzer(ICAnalyzer, _name='ic_analyzer', period=10)
```

### 报表（report.py）
- 汇总内置/自定义分析器结果并输出对比表（转置展示，指标为行）

### 常见问题
- 分位点为何放在策略里？分位点是通用变换，保持指标“纯计算”、策略“决策组合”的单一职责
- 为什么 IC 可能为 NaN？样本不足、信号/收益为常数列或包含 inf/NaN。请检查清洗与样本门槛
- 盈亏比异常大？交易次数过少

### 参考阈值（示例）
- 分位点交易：买入 0.8，卖出 0.2
- z-score 交易：买入 0.7，卖出 -0.7（可结合 r² 最小阈值过滤，如 0.6/0.8）

### 版权与声明
本目录示例用于学习与研究，实际交易请结合风控与品种特性审慎调整。


