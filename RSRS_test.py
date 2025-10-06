from calendar import c
import pandas as pd
import numpy as np
import scipy
import warnings
import matplotlib.pyplot as plt
import backtrader as bt
from strategy import *
from report import generate_performance_report
from analyzer import ICAnalyzer
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

warnings.filterwarnings('ignore')

#导入excel或者csv数据
data=pd.read_csv('Trading_Strategy_Practice-main\data\data_cache_AkshareETFLoader_512800_20200101_20250131.csv',
                    index_col='datetime',parse_dates=['datetime'])
# 选择需要的列
standard_cols = ["open", "high", "low", "close", "volume"]
data=data[standard_cols]

strategy_list={'RSRSBaseStrategy':RSRSBaseStrategy,
                'RSRSRankStrateg':RSRSRankStrategy,'RSRSZscoreStrategy':RSRSZscoreStrategy,
                'RSRSRevisedStrategy':RSRSRevisedStrategy,'RSRSRightSkewedStrategy':RSRSRightSkewedStrategy
                }

results_summary=[]
print("--- 开始批量运行回测 ---")
for name,strategy in strategy_list.items():
    print(f"\n=== 运行策略：{name} ===") 
    cerebro=bt.Cerebro()
    # 加载数据到datafeed中，backtrader才能使用，这是执行策略必要的两步之一
    data_feed=bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)
    cerebro.addstrategy(strategy)
    cerebro.broker.set_cash(100000)
    # --- 因子有效性分析阶段：无交易成本 ---
    # 添加你规划的一系列分析器
    cerebro.addanalyzer(bt.analyzers.Returns,_name='returns')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,_name='sharpe_ratio',timeframe=bt.TimeFrame.Days, compression=252, riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TimeReturn,_name='timeret')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer,_name='trade')
    cerebro.addanalyzer(ICAnalyzer,_name='ic_analyzer')
    # 运行回测
    results=cerebro.run()
    strat=results[0]
    # 从分析器提取结果
    report=generate_performance_report(strat)
    report['strategy_name']=name
    results_summary.append(report)
# 循环结束后只打印一次总表
if results_summary:
    summary_df = pd.DataFrame(results_summary).set_index("strategy_name")
    pd.options.display.float_format = '{:.3f}'.format
    print(summary_df.T) # 使用 .T 进行转置，让指标作为行，更方便对比
else:
    print("没有回测结果可供分析。")

