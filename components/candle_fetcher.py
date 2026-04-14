import requests
import efinance as ef
from components.chrome_driver import ChromeDriver
from models.candle import Candle, CandlePlus
from models.symbol import Symbol
from datetime import datetime, timedelta


class CandleFetcher:

    def __init__(self):
        self.efinance_api_failed = 0
        self.xueqiu_login = False

    def _xueqiu_login(self, chrome):
        if chrome is not None and not self.xueqiu_login:
            chrome.access('https://xueqiu.com/')
            ele = chrome.element('//a[text()="关了灯都一样"]', timeout=10)
            if ele is None:
                chrome.click('//a[contains(text(),"账号密码登录")]')
                chrome.input('//input[@placeholder="请输入手机号或者邮箱"]', '13631367271')
                chrome.input('//input[@placeholder="请输入登录密码"]', 'hsy841121')
                chrome.click('//span[contains(text(),"阅读并同意")]/../i')
                chrome.click('//div[text()="登    录"]')
                ele = chrome.element('//a[text()="关了灯都一样"]', timeout=300)
            self.xueqiu_login = (ele is not None)
        return self.xueqiu_login

    def _xueqiu_data(self, code, freq, begin, lim):
        """
        k线数据源：https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=SZ002727&begin=1749949943802&period=day&type=before&count=-284&indicator=kline
        "type": "d1,fd1,bd1,w,fw,bw,m,fm,bm,y,fy,by"
        """
        cds = []
        chrome = ChromeDriver(port=9222)
        if chrome.driver is None:
            return cds

        self._xueqiu_login(chrome)
        if freq == 5:
            k_type = '5m'
        elif freq == 15:
            k_type = '15m'
        elif freq == 30:
            k_type = '30m'
        elif freq == 60:
            k_type = '60m'
        elif freq == 120:
            k_type = '120m'
        elif freq == 102:
            k_type = 'week'
        elif freq == 103:
            k_type = 'month'
        else:
            k_type = 'day'
        region = 'SH' if code.startswith('6') else 'SZ'
        url = f'https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol={region}{code}&begin={begin}&period={k_type}&type=before&count=-{lim}&indicator=kline'
        json_data = chrome.fetch_data(url)
        # print(json_data)
        k_list = json_data['item']
        print('xueqiu candles [{}] size:'.format(code), len(k_list))
        for k in k_list:
            fms = "%Y-%m-%d" if freq in [101, 102, 103] else "%Y-%m-%d %H:%M:%S"
            dt = datetime.fromtimestamp(k[0] / 1000).strftime(fms)
            c = Candle.new(code, freq)
            c.dt = dt
            c.open = k[2]
            c.high = k[3]
            c.low = k[4]
            c.close = k[5]
            if freq in [101, 102, 103]:
                c.volume = k[1]
                c.chg = k[6]
                c.percent = k[7]
                c.turn = k[8]
                c.turnover = k[9]
            cds.append(c)
        chrome.quit()
        return cds

    @staticmethod
    def _cls_data(code, freq, limit=150):
        """
        k线数据源：https://x-quote.cls.cn/quote/stock/kline?limit=50&secu_code=sz002583&type=fd1
        "type": "d1,fd1,bd1,w,fw,bw,m,fm,bm,y,fy,by"
        """
        cds = []
        region = 'sh' if code.startswith('6') else 'sz'
        url = f'https://x-quote.cls.cn/quote/stock/kline?limit={limit}&secu_code={region}{code}&type=fd1'
        json_data = requests.get(url).json()
        # print(json_data)
        k_list = json_data['data']
        print('cls candles [{}] size:'.format(code), len(k_list))
        for k in k_list:
            c = Candle.new(code, freq)
            data_str = str(k['date'])
            c.dt = f'{data_str[0:4]}-{data_str[4:6]}-{data_str[6:8]}'
            c.open = k['open_px']
            c.high = k['high_px']
            c.low = k['low_px']
            c.close = k['close_px']
            c.volume = k['business_amount']
            c.chg = k['amp']
            c.percent = k['change']
            c.turn = k['tr']
            c.turnover = k['business_balance']
            cds.append(c)
        return cds

    def _efinance_api_data(self, code, freq, begin_dt=None):
        cds = []
        try:
            if self.efinance_api_failed > 10:
                return cds

            if begin_dt is not None:
                if begin_dt.find(':') > 0:
                    sdt = datetime.strptime(begin_dt, '%Y-%m-%d %H:%M')
                else:
                    sdt = datetime.strptime(begin_dt, '%Y-%m-%d')
                begin = sdt.strftime('%Y%m%d')
            else:
                begin = (datetime.now() - timedelta(days=int(160 / (240 / freq) / 5 * 7))).strftime('%Y%m%d')

            df = ef.stock.get_quote_history(code, klt=freq, beg=begin)
            if len(df) > 160:
                df = df.tail(160)

            df.columns = ['name', 'code', 'dt', 'open', 'close', 'high', 'low', 'volume', 'amount',
                          'zf', 'zdf', 'zde', 'turn']
            # df.drop(['name', 'code', 'zf'], axis=1, inplace=True)
            print('efinance api candles [{}] size:'.format(code), len(df))
            for i, k in df.iterrows():
                c = Candle.new(code, freq)
                c.dt = k['dt']
                c.open = k['open']
                c.high = k['high']
                c.low = k['low']
                c.close = k['close']
                c.volume = k['volume']
                c.chg = k['zde']
                c.percent = k['zdf']
                c.turn = k['turn']
                c.turnover = k['amount']
                cds.append(c)
        except Exception as ex:
            print('efinance api fetch candles [{}] error!'.format(code), ex)
        self.efinance_api_failed = 0 if len(cds)>0 else (self.efinance_api_failed+1)
        return cds

    def fetch_candles(self, code, freq=101, lim=160, save=True):
        lcd = Candle.latest(code, freq)
        if lcd and not self.need_fetch(lcd):
            return []

        begin_dt = None
        if lcd is not None:
            begin_dt = lcd.dt
            if freq in [101, 102, 103]:
                ldt = datetime.strptime(begin_dt, "%Y-%m-%d")
                lim = int((datetime.now().timestamp() - ldt.timestamp()) / (60 * 60 * 24))
            else:
                bs = begin_dt.split(':')
                if len(bs) > 2:
                    begin_dt = '{}:{}'.format(bs[0], bs[1])
                ldt = datetime.strptime(begin_dt, "%Y-%m-%d %H:%M")
                lim = int((datetime.now().timestamp() - ldt.timestamp()) / (60 * 60 * 24) * (240 / freq))
        lim = 160 if lim > 160 else lim

        cds = self._efinance_api_data(code, freq, begin_dt=begin_dt)
        if not cds:
            if freq in [101, 102, 103]:
                print(f'efinance api failed. fetch {freq} data from cls.com')
                cds = self._cls_data(code, freq, limit=lim)
            else:
                print(f'efinance api failed. fetch {freq} data from xueqiu.com')
                begin = f'{int(datetime.now().timestamp() * 1000)}'
                cds = self._xueqiu_data(code, freq, begin, lim)
        if save:
            for c in cds:
                if len(c.dt) > 16:
                    c.dt = c.dt[:16]
                if not c.exists():
                    c.created = datetime.now()
                    c.save()
        return cds

    @staticmethod
    def need_fetch(lcd):
        sym = Symbol.select().where(Symbol.code == lcd.code).get()
        if sym:
            ltd = sym.ltd
            ltd_date = datetime.strptime(ltd, "%Y-%m-%d").date()
            today = datetime.today()
            if today.weekday() not in [5, 6] and ltd_date != today.date():
                return True
            ldt = lcd.dt
            if len(ldt) == 16:
                ltd = '{} 15:00'.format(ltd)
            elif len(ldt) == 19:
                ltd = '{} 15:00:00'.format(ltd)
            if ltd == ldt:
                return False
        return True

