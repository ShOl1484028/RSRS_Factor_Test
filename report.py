import pandas as pd
import numpy as np

def generate_performance_report(strat):
    """
    根据回测策略实例，生成一份全面的性能报告。
    """
    # 1. 从内置分析器中提取原始数据
    try:
        returns_analysis=strat.analyzers.returns.get_analysis()
        drawdown_analysis=strat.analyzers.drawdown.get_analysis()
        trade_analysis=strat.analyzers.trade.get_analysis()
        sharpe_analysis = strat.analyzers.sharpe_ratio.get_analysis()
        timereturn_analysis = strat.analyzers.timeret.get_analysis()
        ic_analysis = strat.analyzers.ic_analyzer.get_analysis()
    except KeyError as e:
        print(f"警告：无法找到分析器 {e}。请确保已添加到 cerebro。")
        return {}
    # 2. 将 TimeReturn 转换为 Pandas Series，这是后续计算的基础
    returns_series = pd.Series(timereturn_analysis)

    # 3. 计算你规划的衍生指标
    # 收益类
    total_return = returns_analysis.get('rtot', 0)
    annual_return = returns_analysis.get('rnorm100', 0)
    
    # 风险类
    max_drawdown = drawdown_analysis.get('max', {}).get('drawdown', 0)
    
    # 稳定性与风险调整收益
    sharpe_ratio = sharpe_analysis.get('sharperatio', 0)
    calmar_ratio = annual_return / (max_drawdown + 1e-6) # Calmar 比率
    
    # 计算下行风险和 Sortino 比率
    downside_returns = returns_series[returns_series < 0]
    downside_std = downside_returns.std() * np.sqrt(252) # 年化下行标准差
    sortino_ratio = (annual_return / 100) / (downside_std + 1e-6) # Sortino 比率
    
    # 收益分布特征
    skewness = returns_series.skew() # 偏度
    kurtosis = returns_series.kurtosis() # 峰度
    
    # 交易特征 (来自 TradeAnalyzer)
    total_trades = trade_analysis.get('total', {}).get('total', 0)
    win_rate = trade_analysis.get('won', {}).get('total', 0) / (total_trades + 1e-6) * 100
    avg_win = trade_analysis.get('won', {}).get('pnl', {}).get('average', 0)
    avg_loss = abs(trade_analysis.get('lost', {}).get('pnl', {}).get('average', 0))
    profit_loss_ratio = avg_win / (avg_loss + 1e-6)
    
    # 信号有效性 (来自我们自定义的 ICAnalyzer)
    # 1. 从策略实例中获取 ICAnalyzer 对象本身
    ic_analyzer_instance = strat.analyzers.ic_analyzer
    # 2. 从对象中读取 period 参数
    period = ic_analyzer_instance.p.period
    # 3. 动态构建正确的键名
    ic_key = f'ic_spearman_p{period}'
    # 4. 使用正确的键名获取值
    ic_value = ic_analysis.get(ic_key, np.nan)

    # 4. 组装成一个字典
    report = {
        '总收益 (%)': total_return * 100,
        '年化收益 (%)': annual_return,
        '最大回撤 (%)': max_drawdown,
        '夏普比率': sharpe_ratio,
        '卡玛比率': calmar_ratio,
        '索提诺比率': sortino_ratio,
        '收益偏度': skewness,
        '收益峰度': kurtosis,
        '总交易次数': total_trades,
        '胜率 (%)': win_rate,
        '平均盈利': avg_win,
        '平均亏损': avg_loss,
        '盈亏比': profit_loss_ratio,
        f'IC (Spearman, p={period})': ic_value
    }
    return report