# Active current portfolio with specified weights for SPY/TLT Rotation and shorting VXX together
import datetime as dt
import numpy as np
import pandas.stats.moments as st
import pandas as pd

# Pre Function for fetch_csv for CBOE Vix Data
def clean_vix(vc):
    vc.columns = ['Date','Open','High','Low','Close']
    vc = vc[1:]
    vc['Date'] = pd.to_datetime(vc['Date'])
    vc.iloc[-1,0] = dt.datetime.today().date()
    vc = vc.set_index(pd.DatetimeIndex(vc['Date']))
    return vc

# Pre Function for fetch_csv where futures data from CBOE is massaged to allow for running of live trades
def clean_data(vc):
    vc.columns = ['Symbol','settle']
    vc['expiry'] = pd.to_datetime(vc['Symbol'].str.split(' ').str.get(1))
    vc['name'] = vc['Symbol'].str.split(' ').str.get(0)
    vc['date'] = dt.datetime.today().date()
    vc['contango'] = 1
    
    # Calculate today, but note that since we are adjusting for lookback bias, we need to change the current date to one day prior
    if get_datetime().to_datetime().date().weekday() == 0:
        today = get_datetime().to_datetime().date() - dt.timedelta(3)
    else:
        today = get_datetime().to_datetime().date() - dt.timedelta(1)
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

    for index, row in vc.iterrows():
        if (row['name'] != 'VX') or (row['expiry'].date() < dt.datetime.today().date()): #curr_third_wed):
            vc.drop(index, inplace = True)

    vc = vc.reset_index()
    del vc['index'], vc['name']
    vc['contango'] = vc.iloc[0,1]/vc.iloc[1,1]
    vc['pct_cont'] = vc['settle'].pct_change().shift(-1)

    i = 0
    for i in range(len(vc)):
        vc['date'][i] = dt.datetime.today().date() - dt.timedelta(i)
        i += 1
    # Column Names: Symbol settle expiry date contango pct_cont
    return vc

def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    # For XIV Portion
    # Pulling front month VIX futures data
    cboe = 'http://cfe.cboe.com/market-data/futures-settlements'
    fetch_csv(cboe, date_column='date', date_format='%Y-%m-%d',
              symbol='vf', pre_func=clean_data)
    # Pulling VIX Spot Data from CBOE site
    cboe_vix = 'http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vixcurrent.csv'
    fetch_csv(cboe_vix,pre_func = clean_vix, date_column = 'Date',
              date_format='%Y-%m-%d',symbol = 'vix')
    
    # Setting up universe for XIV
    context.xiv = sid(40516)
    context.xiv_weight = 0.23
    context.xiv_threshold = 0.95
    context.max_vix = 30
    
    # XIV Stop Loss Block
    context.stop_loss_threshold = 0.98 # Threshold for stop loss
    context.buyback_threshold = 0.975 # Threshold for buying back after stoploss
    context.augen_period = 21 # Rolling augen standard deviation period
    context.augen_threshold = -1.5 # Threshold for not buying back if SPY drops
    time_interval = 30 # Time interval in minutes to count rhough
    total_minutes = 6*60 + (60 - time_interval)
    # This will start at 9:31AM and will run every 30 minutes
    for i in range(1, total_minutes):
        # Every 30 minutes run schedule
        if (i == 1) or (i % time_interval == 0):
            schedule_function(stop_loss, date_rules.every_day(), time_rules.market_open(minutes=i),True)
    # Schedules one more stop loss to be called 1 minute before close
    schedule_function(stop_loss, date_rules.every_day(), time_rules.market_close(minutes=1))
    
    # Setting up universe for SPY/TLT
    context.spy = sid(8554)
    context.spy_long = 220
    context.spy_short = 25
    context.spy_threshold = 0.99
    
    context.tlt = sid(23921)
    context.tlt_long = 70
    context.tlt_short = 35
    
    context.spy_weight = 0.50
    context.tlt_weight = 0
        
    # Setting Trade Guards
    set_long_only()
        
    # Rebalance every day, 5 minute after market open.
    schedule_function(my_rebalance, date_rules.every_day(),
                      time_rules.market_open(hours = 0, minutes = 5))

def maturities(context,data):
    
    # Calculate today, but note that since we are adjusting for lookback bias, we need to change the current date to one day prior
    if get_datetime().to_datetime().date().weekday() == 0:
        today = get_datetime().to_datetime().date()# - dt.timedelta(3)
    else:
        today = get_datetime().to_datetime().date()# - dt.timedelta(1)
    curr_month = today.month
    curr_year = today.year
    
    # Finding Prev Third Wed
    curr_eigth_day = dt.date(curr_year,curr_month,7)
    curr_second_day = dt.date(curr_year,curr_month,3).weekday()
    curr_third_fri = curr_eigth_day - dt.timedelta(curr_second_day) + dt.timedelta(14)
    last_third_wed = curr_third_fri - dt.timedelta(30)
    
    # Finding Next Third Wed
    if curr_month == 12:
        next_month = 2
        next_year = curr_year + 1
    elif curr_month == 11:
        next_month = 1
        next_year = curr_year + 1
    else:
        next_month = curr_month + 2
        next_year = curr_year
    next_eigth_day = dt.date(next_year,next_month,7)
    next_second_day = dt.date(next_year,next_month,3).weekday()
    next_third_fri = next_eigth_day - dt.timedelta(next_second_day) + dt.timedelta(14)
    next_third_wed = next_third_fri - dt.timedelta(30)
    
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
    
    # Finding Term: When current date is after expiry, should be 100% of spot/f1
    if today <= curr_third_wed:
        dte = curr_third_wed - today
        term = curr_third_wed - last_third_wed
    else:
        dte = next_third_wed - today
        term = next_third_wed - curr_third_wed
    # print (float(dte.days)/term.days)
    front_weight = float(dte.days)/term.days
    return front_weight
    
# Before each trading day, calculate all necessary SMA and Ratios
def before_trading_start(context,data):
    spot_wgt = maturities(context,data)
    front_wgt = 1 - spot_wgt
    print "Front weight: %.4f" %spot_wgt
    
    # Logging Key Notes
    settle = data.current('vf','settle')
    contango = data.current('vf','contango')
    vix_close = float(data.current('vix','Close'))
    print "Settlement: " + str(settle) + " Contango: " + str(contango) + " VIX Close: " + str(vix_close)
    
    # Calculating Ratio for VIX/F1
    vixf1 = vix_close/data.current('vf','settle')
    
    context.xiv_ratio = spot_wgt*vixf1 + front_wgt*contango
    context.xiv_signal = (context.xiv_ratio < context.xiv_threshold) and (vix_close < context.max_vix)
    log.info("Normalized Ratio: %.2f" %context.xiv_ratio)
    print "Normalized Ratio: " + str(context.xiv_ratio)
    
    # XIV Stop Loss Triggers Initiation
    context.stop_loss_initializer = False
    context.stop_loss_not_triggered = True
    context.buyback_not_triggered = True
    
    # XIV Buyback Triggers
    spy_hist =data.history(context.spy,'close',context.augen_period + 1,'1d')
    log_returns = np.log(spy_hist) - np.log(spy_hist.shift(1))
    daily_vol = st.rolling_std(log_returns, context.augen_period, ddof = 1)
    daily_vol_dollar = daily_vol*spy_hist
    context.dollar_vol = daily_vol_dollar.ix[-1]
    
    # Calculating SPY SMA 25-220
    spy_hist = data.history(context.spy,'close',context.spy_long,'1d')
    context.spy_long_sma = spy_hist.mean()
    context.spy_shrt_sma = spy_hist.tail(context.spy_short).mean()
    context.spy_signal = context.spy_shrt_sma > context.spy_long_sma
    context.last_spy_price = data.current(context.spy,'close')
    log.info("Last SPY Close: %.2f SPY_Long: %.2f SPY_Short: %.2f" %(context.last_spy_price,context.spy_long_sma,context.spy_shrt_sma))
    
    # Calculating TLT SMA 35-70
    tlt_hist = data.history(context.tlt,'close',context.tlt_long,'1d')
    context.tlt_long_sma = tlt_hist.mean()
    context.tlt_shrt_sma = tlt_hist.tail(context.tlt_short).mean()
    context.tlt_signal = context.tlt_shrt_sma > context.tlt_long_sma
    last_tlt_price = data.current(context.tlt,'close')
    log.info("Last TLT Close: %.2f TLT_Long: %.2f TLT_Short: %.2f" %(last_tlt_price,context.tlt_long_sma,context.tlt_shrt_sma))

# XIV Stop loss order function block
def stop_loss(context, data):
    # This condition is called every 30 minutes starting from 10 am
    if context.xiv_signal and context.stop_loss_not_triggered and context.stop_loss_initializer:
        # Pulls current price of XIV
        context.current_price = data.current(context.xiv, 'price')
        # Computes the current price change of XIV
        context.price_change = context.current_price/context.open_price
        print "XIV Percent Change: %.4f" %(context.price_change-1)
        # If the price change dropped below threshold, execute this condition
        if context.price_change < context.stop_loss_threshold:
            if context.xiv in context.portfolio.positions:
                log.info("Stop loss reached - %.4f" %(context.price_change-1))
                # Closes XIV positions and stops any trading of XIV for the day
                order_target_percent(context.xiv, 0)
                # Sets the denominator for price changes to stop-loss price
                context.open_price = context.current_price
                context.stop_loss_not_triggered = False
    # Initialize stop loss parameter for opening price
    if not context.stop_loss_initializer:
        # This statement called once at the beginning of day at 9:31 am to instantiate price point
        context.stop_loss_initializer = True
        context.open_price = data.current(context.xiv,'open')
    # This condition is called every 30 minutes if the stoploss has been reached
    if (context.stop_loss_not_triggered == False) and context.buyback_not_triggered:
        if context.xiv_signal:
            # Pulls current price for XIV
            context.current_price = data.current(context.xiv, 'price')
            # Computes the current price change of XIV given the stop-loss price
            context.drop_price_change = context.current_price/context.open_price
            # Computes the Augen Price vol of SPY
            context.spy_diff = data.current(context.spy, 'price')-context.last_spy_price
            context.augen_vol = context.spy_diff/context.dollar_vol
            context.augen_trigger = context.augen_vol > context.augen_threshold
            # If the price change dropped below the buyback threshold
            # and SPY does not drop below 1% of it's close price from yesterday,
            # buyback VXX
            context.buyback_trigger = context.drop_price_change < context.buyback_threshold
            print "XIV Post Drop Change: %.4f" %(context.drop_price_change-1)
            if context.buyback_trigger and context.augen_trigger:
                log.info("Buyback reached - %.4f" %(context.drop_price_change-1))
                # Purchase XIV following standard protocol
                target_xiv_mv = context.portfolio.portfolio_value*context.xiv_weight
                order_target_value(context.xiv,target_xiv_mv)
                context.buyback_not_triggered = False
                print "SPY Change on buyback: %.4f" %(context.augen_vol-1)
                # Sets the denominator for price changes to buyback price
                # Used only if preference is to have another stoploss iteration
                context.open_price = context.current_price
                # context.stop_loss_not_triggered = True
                
# Rebalancing function for ordering
def my_rebalance(context,data):
        
    # XIV Trading
    if context.xiv_signal:
        if context.xiv in context.portfolio.positions:
            log.info("Already holding XIV: %.2f"%context.xiv_ratio)
        else:
            if data.can_trade(context.xiv):
                target_xiv_mv = context.portfolio.portfolio_value*context.xiv_weight
                order_target_value(context.xiv,target_xiv_mv)
                log.info("Long XIV - Bought %.2f"%target_xiv_mv)
    else:
        if data.can_trade(context.xiv):
            order_target_percent(context.xiv,0)
        log.info("XIV Move to Cash - %.2f"%context.xiv_ratio)
        
    # SPY Trading
    if context.spy_signal:
        if context.spy in context.portfolio.positions:
            log.info("Already holding SPY - Fast %.2f"%context.spy_shrt_sma)
        else:
            target_spy_mv = context.portfolio.portfolio_value*context.spy_weight
            order_target_value(context.spy,target_spy_mv)
            log.info("Long SPY - Bought %.2f"%target_spy_mv)
    else:
        order_target_percent(context.spy,0)
        log.info("SPY Move to Cash - Fast %.2f"%context.spy_shrt_sma)
   
    # TLT Trading
    if context.tlt_signal:
        if context.tlt in context.portfolio.positions:
            log.info("Already holding TLT - Fast %.2f"%context.tlt_shrt_sma)
        else:
            target_tlt_mv = context.portfolio.portfolio_value*context.tlt_weight
            order_target_value(context.tlt,target_tlt_mv)
            log.info("Long TLT - Bought %.2f"%target_tlt_mv)
    else:
        order_target_percent(context.tlt,0)
        log.info("TLT Move to Cash - Fast %.2f"%context.tlt_shrt_sma)
        
def handle_data(context,data):
    pass