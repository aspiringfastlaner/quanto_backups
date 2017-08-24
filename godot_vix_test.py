'''
Godot Finance VX Futures: http://www.godotfinance.com/pdf/VIXFuturesBasisTrading_2_Rev1.pdf

Calculate roll ratio as:

R(t) = ((VXF(t) – VIX(t))/VXFVola(t))/TTS(t)
    where,
    R(t) is the roll ratio
    VXF(t) is the futures price
    VIX(t) is the VIX spot
    TTS(t) is the days to expiry of the front month futures contract
    and
    VXFVola(t) = sqrt(sum(DeltaVXF(t-i)^2)/10) i=0...9
 
If the ratio is over 0.12, we short the front month VX future.
If we're shorting the font month and the ratio is 0.10 or below, we buy back the VX future.
If the maturity is less than 10 trading days, the future is sold back.
'''

import numpy as np
import scipy as sp
from quantopian.algorithm import order_optimal_portfolio
import quantopian.experimental.optimize as opt
from quantopian.algorithm import calendars
import datetime as dt
import pandas.stats.moments as st

from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.factors import CustomFactor
from quantopian.pipeline.data.quandl import cboe_vix

# pipeline custom factor for cboe_vix
class GetVIX(CustomFactor):
    window_length = 1
    def compute(self, today, assets, out, vix):
        out[:] = vix[0]

def initialize(context):

    # Get continuous futures for VX...
    context.future = continuous_future('VX', adjustment = None)
    
    # Pulling VIX Spot data
    my_pipe = Pipeline()
    attach_pipeline(my_pipe, 'my_pipeline')
    my_pipe.add(GetVIX(inputs=[cboe_vix.vix_open]), 'vix')
    
    # Schedule function for stop loss 
    '''
    time_interval = 30
    
    total_minutes = 6*60 + (60 - time_interval)
    
    for i in range(1, total_minutes):
        # Every 30 minutes run schedule
        if (i == 1) or (i % time_interval == 0):
            # This will start at 9:31AM and will run every 30 minutes
            schedule_function(rebalance, date_rules.every_day(), time_rules.market_open(minutes=i))#,calendar=calendars.US_EQUITIES)
    '''
    
    # Rebalance function for trading VX futures
    schedule_function(rebalance, 
                      date_rules.every_day(), 
                      time_rules.market_open(minutes = 30), 
                      calendar=calendars.US_EQUITIES)
    
    context.enter_roll = 0.12
    context.exit_roll = 0.10
    context.lvg = 0.6
    
def calculate_ratio(context,data):
    
    # Pulling spot vix
    vix = context.vix
    
    vx_hist = data.history(context.vx_future, 'price', 10, '1d')
    
def rebalance(context, data):
    # Initializing today to calculate TTS
    today = get_datetime().to_datetime().date()
    
    # Pulling the current continuous VX futures chain
    vx_chain = data.current_chain(context.future)
    
    # Determining the Future with the highest roll and more than 10 days to expiry
    
    context.vx_future = vx_chain[0]
    context.vx_contract = data.current(context.future, 'contract')
    fut_tts = context.vx_future.end_date.to_datetime().date() - today
    fut_tts = int(fut_tts.days)
    
    cpp = context.portfolio.positions
    cpp_symbols = map(lambda x: x.symbol, cpp)
    if len(cpp_symbols) > 0:
        if cpp_symbols[0] != context.vx_contract.symbol:
            order(context.current_holdings, 0)
    
    if fut_tts > 10:
        if context.vx_contract in context.portfolio.positions:
            pass
        else:
            order(context.vx_contract, -1)
            context.current_holdings = context.vx_contract
    else:
        order(context.vx_contract, 0)
    
    
    
    