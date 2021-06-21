##ETH
class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['ETH-USDT'],
            },
        }
        self.time_base = 10
        self.period = self.time_base * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_short_buy = 5
        self.ma_short_sell = 15

        self.buy_rate = 0.006
        self.sell_rate = 0.01
        self.stock_base = 80
        self.last_price = float('inf')  
    
    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        target_currency = pair.split('-')[0]  #ETH
        base_currency = pair.split('-')[1]  #USDT
        USDT_amount = self['assets'][exchange][base_currency] 
        BTC_amount = self['assets'][exchange][target_currency] 
        target_currency_amount = self['assets'][exchange][target_currency] 

        close_price = information['candles'][exchange][pair][0]['close']
        present_price = information['candles'][exchange][pair][0]['close']
        volume = information['candles'][exchange][pair][0]['volume']
        high_price = information['candles'][exchange][pair][0]['high']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])

        # calculate current ma cross status
        s_ma_buy = talib.SMA(self.close_price_trace, self.ma_short_buy)[-1]
        s_ma_sell = talib.SMA(self.close_price_trace, self.ma_short_sell)[-1]
        #Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['BTC']) + ',USDT' + str(self['assets'][exchange]['USDT']))
        if close_price >= 2200 and close_price <= 3100:
            if close_price < 2450:
                Log('buying unit of ' + str(target_currency))
                self.last_type = 'buy'
                money = self['assets'][exchange]['USDT']
                if close_price < 2300:
                    money_amount = money/2300
                else:
                    money_amount = self.stock_base * (close_price-2300) / 2300
                return [
                    {
                        'exchange': exchange,
                        'amount': money_amount,
                        'price': 2300,
                        'type': 'LIMIT',
                        'pair': pair,
                    }
                ]
            # cross down
            elif close_price > 2700:
                Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
                self.last_type = 'sell'
                if close_price > 3000:
                    money_amount = target_currency_amount
                else:
                    money_amount = self.stock_base * (close_price-2700) / 2700
                return [
                    {
                        'exchange': exchange,
                        'amount': -money_amount,
                        'price': 2700,
                        'type': 'LIMIT',
                        'pair': pair,
                    }
                ]    
        else:
            # below MA buy
            if (s_ma_buy - present_price)/s_ma_buy >= self.buy_rate and USDT_amount > 0.0 and self.last_price > present_price:
                
                self.last_type = 'buy'
                buy_volume = self.stock_base * (s_ma_buy - present_price)/s_ma_buy
                self.last_price = present_price
                buy = min(buy_volume, USDT_amount/present_price)

                Log('buy_volume: ' + str(buy_volume) + ', amount: ' + str(USDT_amount/present_price))
                Log('buying ' + str(buy) + ' unit of ' + str(target_currency))

                if buy > USDT_amount:
                    return[]

                return [
                    {
                        'exchange': exchange,
                        'amount':  buy,
                        'price': -1,
                        'type': 'MARKET',   
                        'pair': pair,                 
                    }
                ]
            # beyond MA sell
            elif (present_price - s_ma_sell)/s_ma_sell >= self.sell_rate and BTC_amount > 0.0 and self.last_price < present_price:
                Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
                Log('selling, ' + exchange + ':' + pair)
                self.last_type = 'sell'

                sell_volume = self.stock_base * (present_price - s_ma_sell)/s_ma_sell + 0.25
                self.last_price = present_price

                sell = min(sell_volume, BTC_amount)
                # if sell > BTC_amount:
                #     return[]
                return [
                    {
                        'exchange': exchange,
                        'amount': -sell,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            # 15%停損
        if present_price < high_price * 0.85 and BTC_amount > 0.0:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'

            sell = BTC_amount
            self.last_price = present_price
                # if sell > BTC_amount:
                #     return []

            return [
                {
                    'exchange': exchange,
                    'amount': -sell,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]        
        return []
   
    def on_order_state_change(self, order):
        Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))
