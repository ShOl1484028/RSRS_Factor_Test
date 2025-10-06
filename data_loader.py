import os
import akshare as ak
import pandas as pd
import backtrader as bt
from abc import ABC, abstractmethod

class BaseDataLoader(ABC):
    def __init__(self, cache_path=None):
        self.cache_path = cache_path

    def load_data(self, **kwargs):
        print(f"📝 加载参数: {kwargs}")
        
        cache_file = self.cache_path or self._make_cache_file(**kwargs)
        print(f"📂 缓存路径: {cache_file}")
        
        if os.path.exists(cache_file):
            # 从缓存读取时，datetime已经是索引，直接返回
            data = pd.read_csv(cache_file, index_col='datetime', parse_dates=['datetime'])
            print(f"✅ 数据加载成功，形状: {data.shape}")
            return data
        else:
            # 从akshare获取时，需要处理列名和索引
            print(" 缓存文件不存在，开始从数据源获取数据...")
            data = self.fetch_data(**kwargs)
            data.to_csv(cache_file)
            print(f"✅ 数据获取并保存成功，形状: {data.shape}")
            return data

    @abstractmethod
    def fetch_data(self, **kwargs):
        """子类实现：从具体数据源拉取原始数据并做预处理，返回DataFrame"""
        pass

    def _make_cache_file(self, **kwargs):
        # 尝试用 fund_code 或 symbol, start_date, end_date 生成文件名
        symbol = kwargs.get('symbol')
        start_date = kwargs.get('start_date', 'start')
        end_date = kwargs.get('end_date', 'end')
        
        # 确保data目录存在
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        filename = f"data_cache_{self.__class__.__name__}_{symbol}_{start_date}_{end_date}.csv"
        return os.path.join(data_dir, filename)

    def transfer_to_datafeed(self, data, required_cols=None):
        """
        将 pandas DataFrame 转换为 Backtrader 可用的数据源。
        
        :param data: pandas DataFrame，索引为 datetime
        :param required_columns: 需要的字段列表（如 ["open", "high", "rsi"]），
                                如果为 None 或只包含标准 OHLCV，则使用标准 PandasData。
        :return: bt.feeds.PandasData 或其子类的实例
        """
        # 0. 确保输入是副本，避免修改原始 DataFrame
        data=data.copy()
        # 1. 定义 backtrader 默认识别的标准列
        standard_cols = ["open", "high", "low", "close", "volume"]
        # 2. 验证标准列的str是否在数据的索引中
        data_list=data.columns.tolist()
        for col in standard_cols:
            if col not in data_list:
                raise ValueError(f"数据中缺少必要的列: {col}")
        # 3. 如果不传入 required_columns列表，则将data中的标准列赋值给data_feed
        if required_cols is None:
            # --- 情况一：没有附加列或附加列为空 ---
            data = data[standard_cols]
            data_feed=bt.feeds.PandasData(dataname=data)
        else:
            # --- 情况二：有附加列 ---
            # 将required_cols中不在standard_cols中的列赋值给custom_cols，建立自定义PandasData类，把custom_cols赋值给lines，把custom_cols赋值给params
            custom_cols=list(set(required_cols)-set(standard_cols))
            class CustomPandasData(bt.feeds.PandasData):
                lines=tuple(custom_cols)
                params={col:-1 for col in custom_cols}#backtrader中的lines和params是类级别的属性，不需要在创建实例时传递;params既可以用字典形式定义，也可以用元组形式定义。这两种方式都是有效的
            data_feed=CustomPandasData(dataname=data)
        return data_feed

class AkshareETFLoader(BaseDataLoader):
    def fetch_data(self,**kwargs):
        symbol = kwargs.get('symbol')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        
        # 检查参数
        if not symbol:
            raise ValueError("fund_code参数不能为空")
        
        data = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="hfq")
        
        # 统一转换为英文列名
        column_map = {
            "日期": "datetime", 
            "收盘": "close", 
            "开盘": "open", 
            "最高": "high", 
            "最低": "low", 
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "change_pct",
            "涨跌额": "change_amount",
            "换手率": "turnover_rate"
        }
        
        # 重命名列
        data = data.rename(columns=column_map)
        
        # 转换日期并设置为索引
        data['datetime'] = pd.to_datetime(data['datetime'])
        data.set_index('datetime', inplace=True)
        
        print(f"📊 数据范围: {data.index.min().date()} 到 {data.index.max().date()}")
        return data

