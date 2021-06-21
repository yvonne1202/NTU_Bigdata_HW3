##BTC
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
            'Bitfinex': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.first = 0
        self.period = 10 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_long = 10
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2
        self.stock_base = 12

    def on_order_state_change(self,  order):
        Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN


    # called every self.period
    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        target_currency = pair.split('-')[0]  #BTC
        base_currency = pair.split('-')[1]  #USDT
        base_currency_amount = self['assets'][exchange][base_currency] 
        target_currency_amount = self['assets'][exchange][target_currency]
        # add latest price into trace
        close_price = information['candles'][exchange][pair][0]['close']
        high_price = information['candles'][exchange][pair][0]['high']
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()
        if cur_cross is None:
            return []
        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []
        # cross up
        if self.first == 0:
            Log('buying 0.5 unit of ' + str(target_currency))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 0.5,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
            self.first = 1
        if close_price < 35500:
            Log('buying 200 unit of ' + str(target_currency))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            money = self['assets'][exchange]['USDT']
            if close_price < 34000:
                money_amount = money / close_price
            else:
                money_amount = self.stock_base * (close_price-34000) / 34000
            return [
                {
                    'exchange': exchange,
                    'amount': money_amount,
                    'price': 34000,
                    'type': 'LIMIT',
                    'pair': pair,
                }
            ]
        # cross down
        elif close_price > 37000:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            if close_price > 40000 :
                money_amount = target_currency_amount
            else:
                money_amount = self.stock_base * (close_price-37000) / 37000
            return [
                {
                    'exchange': exchange,
                    'amount': -money_amount,
                    'price': 37000,
                    'type': 'LIMIT',
                    'pair': pair,
                }
            ]
        # 15%停損
        if close_price < high_price * 0.85 and target_currency_amount > 0.0:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'

            sell = target_currency_amount
            self.last_price = close_price
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
        self.last_cross_status = cur_cross
        return []
