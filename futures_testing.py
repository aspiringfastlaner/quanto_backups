import numpy as np
import scipy as sp
from quantopian.algorithm import order_optimal_portfolio
import quantopian.experimental.optimize as opt
from quantopian.algorithm import calendars
import datetime as dt
import pandas.stats.moments as st


def initialize(context):

    # Get continuous futures for VX...
    context.future = continuous_future('VX', adjustment = None)
    
    time_interval = 30
    
    total_minutes = 6*60 + (60 - time_interval)
    
    for i in range(1, total_minutes):
        # Every 30 minutes run schedule
        if (i == 1) or (i % time_interval == 0):
            # This will start at 9:31AM and will run every 30 minutes
            schedule_function(rebalance, date_rules.every_day(), time_rules.market_open(minutes=i),calendar=calendars.US_EQUITIES)
    
    context.vxx = sid(38054)
    context.threshold = 0.975
    context.vxx_pct = 1
    context.can_trade = False
    
def before_trading_start(context,data):
    
    '''
    F January
    G February
    H March
    J April
    K May
    M June
    N July
    Q August
    U September
    V October
    X November
    Z December
    '''
    
    month_dict = {1:'F', 2:'G', 3:'H',
                 4:'J', 5:'K', 6:'M',
                 7:'N', 8:'Q', 9:'U',
                 10:'V', 11:'X', 12:'Z'}
    
    if get_datetime().to_datetime().date().weekday() == 0:
        today = get_datetime().to_datetime().date() - dt.timedelta(3)
    else:
        today = get_datetime().to_datetime().date() - dt.timedelta(1)
        
    today = get_datetime().to_datetime().date()
    
    curr_month = today.month
    curr_year = today.year
    
    # Finding Cur Third Wed
    if curr_month == 12:
        next_month = 1
        next_year = curr_year + 1
    else:
        next_month = curr_month + 1
        next_year = curr_year
    next_eigth_day = dt.date(next_year,next_month,7)
    next_second_day = dt.date(next_year,next_month,3).weekday()
    next_third_fri = next_eigth_day - dt.timedelta(next_second_day) + dt.timedelta(14)
    curr_third_wed = next_third_fri - dt.timedelta(30)
    
    if today <= curr_third_wed:
        month_key = month_dict[int(curr_month)]
        year_val = str(curr_year)
        
        if int(curr_month) == 12:
            f2_month_key = month_dict[1]
            f2_year_val = str(int(curr_year) + 1)
        else:
            f2_month_key = month_dict[int(curr_month) + 1]
            f2_year_val = str(curr_year)
    else:
        if int(curr_month) == 12:
            month_key = month_dict[1]
            f2_month_key = month_dict[2]
            
            year_val = str(int(curr_year) + 1)
            f2_year_val = year_val
        else:
            month_key = month_dict[int(curr_month) + 1]
            year_val = str(curr_year)
            
            if int(curr_month) == 11:
                f2_month_key = month_dict[1]
                f2_year_val = str(int(curr_year) + 1)
            else:
                f2_month_key = month_dict[int(curr_month) + 2]
                f2_year_val = str(curr_year)
    
    context.f1_symbol = 'VX' + month_key + year_val[2:]
    context.f2_symbol = 'VX' + f2_month_key + f2_year_val[2:]
    
    #print f1_symbol
    #print f2_symbol
    
    #context.f1 = future_symbol(f1_symbol)
    #context.f2 = future_symbol(f2_symbol)
           
def rebalance(context, data):
    vx_chain = data.current_chain(context.future)
    front_contract = vx_chain[0]
    secondary_contract = vx_chain[1]
    tertiary_contract = vx_chain[2]
    
    f1_price = data.current(front_contract, 'price')
    f2_price = data.current(secondary_contract, 'price')
    signal = f1_price/f2_price <= context.threshold
    if signal:
        if context.vxx in context.portfolio.positions:
            pass
        else:
            # Calculating the number of shares of VXX to short to reach the target
            # portfolio percentage allocation
            target_mv = context.portfolio.portfolio_value*context.vxx_pct
            order_target_value(context.vxx,-target_mv)
    else:
        order_target_percent(context.vxx,0)
            
    record(signal=f1_price/f2_price)
    
    print front_contract.end_date.to_datetime().date()
    print secondary_contract.end_date.to_datetime().date()
    print tertiary_contract.end_date.to_datetime().date()