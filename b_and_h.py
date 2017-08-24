import numpy as np
# SPY  GLD SHY TLT
# https://portfoliocharts.com/portfolios/
def initialize(context):
    
    context.jnj = sid(4151)
    context.pg = sid(5938)
    context.ko = sid(4283)
    context.mmm = sid(4922)
    context.low = sid(4521)
    context.cl = sid(1582)
    context.emr = sid(2530)
    
    context.weight = 1.0/7.0
    set_benchmark(sid(8554))
    #Permanent Portfolio 
    
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(hours = 0, minutes = 1))

def my_rebalance(context, data):
    
    
    if len(context.portfolio.positions) > 0:
        pass
    else:
        order_target_percent(context.jnj, context.weight)
        order_target_percent(context.pg, context.weight)
        order_target_percent(context.ko, context.weight)
        order_target_percent(context.mmm, context.weight)
        order_target_percent(context.low, context.weight)
        order_target_percent(context.emr, context.weight)
        