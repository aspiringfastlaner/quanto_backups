"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters.morningstar import Q1500US
import numpy as np
import datetime
 
def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.month_start(), time_rules.market_open(minutes = 5))
     
    # Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.month_start(), time_rules.market_open(minutes = 5))
     
    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')
         
def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    
    # Base universe set to the Q500US
    base_universe = Q1500US()

    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest
     
    pipe = Pipeline(
        screen = base_universe,
        columns = {
            'close': yesterday_close,
        }
    )
    return pipe
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')
    
    # Query for securities based on PE ratio and their economic sector
    fundamental_df = get_fundamentals(
        # Retrieve data based on PE ratio and economic sector
        query(
            fundamentals.earnings_ratios.dps_growth,
            fundamentals.earnings_report.dividend_per_share,
        )

        # Filter where the Sector code matches our technology sector code
        #.filter(fundamentals.asset_classification.morningstar_sector_code == 311)

        # Filter where PE ratio is greater than 20 
        #.filter(fundamentals.valuation_ratios.pe_ratio > 20)

        # Filter where PE ratio is less than 50
        #.filter(fundamentals.valuation_ratios.pe_ratio < 50)
		.filter(fundamentals.earnings_ratios.dps_growth > 0)
        # Order by highest PE ratio and limit to 4 results 
        .order_by(fundamentals.valuation.market_cap.desc()).limit(500)
        
        )
    #print fundamental_df.head().columns[:6]
    #print fundamental_df.head()
    
    # These are the securities that we are interested in trading each day.
    context.security_list = fundamental_df.head().columns[:11]
     
def my_assign_weights(context, data):
    """
    Assign weights to securities that we want to order.
    """
    pass
 
def my_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    
    date = get_datetime()
    month = date.month
    if month%6 == 1:
        #Resetting portfolio
        for security in context.portfolio.positions:
            if security not in context.security_list and data.can_trade(security):
                order_target_percent(security, 0)
        
        #Calculating percentage of portfolio for allocation
        percent = 1.00 / float(len(context.security_list))
        
        #Doing the annual trades
        for security in context.security_list:
            if data.can_trade(security):
                order_target_percent(security, percent)
        
        print(month)
 
def my_record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    pass
 
def handle_data(context,data):
    """
    Called every minute.
    """
    pass
