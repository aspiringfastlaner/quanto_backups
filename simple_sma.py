import datetime as dt
import numpy as np
import pandas as pd
import pandas.stats.moments as st

def initialize(context):
    
    context.stock_long = 110
    context.stock_short = 35
        
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(hours=0,minutes=5))
    context.stock = sid(32620)
    set_benchmark(sid(23921))
    
def before_trading_start(context,data):
    
    # Finding SMA
    stock_hist = data.history(context.stock,'close',context.stock_long,'1d')
    context.long_sma = stock_hist.mean()
    context.shrt_sma = stock_hist.tail(context.stock_short).mean()    
    context.signal = context.shrt_sma >= context.long_sma
    
    
def my_rebalance(context,data):
    
    if context.signal:
        if context.stock in context.portfolio.positions:
            pass
        else:
            pass
        target_mv = context.portfolio.portfolio_value
        order_target_value(context.stock,target_mv)
    else:
        order_target_percent(context.stock,0)
        
    last_price = data.current(context.stock,'price')
    record(short = context.shrt_sma, lng = context.long_sma, last_price = last_price)
    