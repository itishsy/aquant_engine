import engines.engine
from engines.engine import job_engine, Fetcher
from models.symbol import Symbol
from datetime import datetime
from components.candle_fetcher import CandleFetcher
from components.chrome_driver import ChromeDriver, By
from models.review import Pan, Hot, Ztb
# from models.ztb import Ztb, Bk
import efinance as ef
import traceback
import requests
import time
from peewee import fn


@job_engine
class Candles(Fetcher):

    def fetch(self):
        cf = CandleFetcher()

        now = datetime.now()
        # freq = [101, 120, 60, 30]
        # freq = [101, 60]
        # if now.weekday() == 5:
        #     freq.append(102)
        # if now.day == 1:
        #     freq.append(103)
        sbs = Symbol.select()
        codes = Hot.find_hot_codes(50)
        count = 0
        for sb in sbs:
            try:
                if sb.code not in codes:
                    continue
                print('[{}] [{}] {} fetch candles start!'.format(datetime.now(), count, sb.code))
                # for f in freq:
                cds = cf.fetch_candles(sb.code)
                print('[{}] [{}] {} fetch {} candles done!'.format(datetime.now(), count, sb.code, len(cds)))
                count = count + 1
            except Exception as ex:
                print('fetch candles [{}] error!'.format(sb.code), ex)
        print('[{}] fetch all done! elapsed time:{}'.format(datetime.now(), datetime.now() - now))


@job_engine
class Symbols(Fetcher):

    def fetch(self):
        df = ef.stock.get_all_company_performance()
        # df = ef.stock.get_realtime_quotes()
        df = df.iloc[:, 0:2]
        df.columns = ['code', 'name']
        stocks = []
        if len(df) > 5000:
            for i, row in df.iterrows():
                code = str(row['code'])
                name = row['name']
                if 'ST' not in name and (code.startswith('00') or code.startswith('60') or code.startswith('30')):
                    stocks.append(code)
                if len(stocks) > 199:
                    sss = ef.stock.get_latest_quote(stocks)
                    for ii, ss in sss.iterrows():
                        Symbol.upset(ss)
                        stocks.clear()
        else:
            symbols = Symbol.select()
            for sym in symbols:
                stocks.append(sym.code)
                if len(stocks) > 199:
                    sss = ef.stock.get_latest_quote(stocks)
                    for ii, ss in sss.iterrows():
                        Symbol.upset(ss)
                        stocks.clear()
        if len(stocks) > 0:
            sss = ef.stock.get_latest_quote(stocks)
            for ii, ss in sss.iterrows():
                Symbol.upset(ss)
                stocks.clear()


def stock_format(stock_str):
    name = stock_str.split('\n')[0].replace(' ', '')
    if name.__contains__('+') or name.__contains__('-'):
        name = name.split('+')[0]
        name = name.split('-')[0]
    ss = Symbol.select().where(Symbol.name == name or Symbol.code == name)
    if len(ss) > 0:
        return '{}|{}'.format(ss[0].name, ss[0].code)
    return ''


def stock_link(stocks, code_key, name_key, price_key=None, change_key=None):
    link_str = ''
    for sto in stocks:
        code = sto[code_key].replace('sz', '').replace('sh', '').replace('SZ', '').replace('SH', '')
        name = sto[name_key]
        if price_key and change_key:
            change = sto[change_key]
            if isinstance(change, float):
                change = '{}%'.format(change if abs(change) > 0.12 else round(change * 100, 2))
            link_str += xueqiu_link(code, name, '{},{}'.format(sto[price_key], change))
        elif price_key:
            link_str += xueqiu_link(code, name, sto[price_key])
        elif change_key:
            change = sto[change_key]
            if isinstance(change, float):
                change = '{}%'.format(change if abs(change) > 0.12 else round(change * 100, 2))
            link_str += xueqiu_link(code, name, change)
        else:
            link_str += xueqiu_link(code, name)
    return link_str


def xueqiu_link(code, name, last=None, change=None):
    block = ''
    if last and change:
        block = '({},{})'.format(last, change)
    elif last:
        block = '({})'.format(last)
    elif change:
        block = '({})'.format(change)
    if code.startswith('60') or code.startswith('68'):
        return "<a href='http://xueqiu.com/S/SH{}'>{}{}</a> ".format(code, name, block)
    else:
        return "<a href='http://xueqiu.com/S/SZ{}'>{}{}</a> ".format(code, name, block)


@job_engine
class Fupan(Fetcher):

    def fetch(self):
        chrome = ChromeDriver()
        try:
            dtn = datetime.now().strftime("%Y-%m-%d")
            if not Pan.select().where(Pan.date == dtn).exists():
                pan = Pan()
                pan.date = dtn
                # 1.指数
                zs_data = chrome.fetch_data(
                    'https://x-quote.cls.cn/v2/quote/a/web/stocks/basic?app=CailianpressWeb&fields=secu_name,secu_code,trade_status,change,change_px,last_px&os=web&secu_codes=sh000001,sz399001,sh000905,sz399006&sv=8.4.6&sign=7ddfd2eef7564087ff01a1782c724f43')
                pan.zs = '{}({}%)'.format(round(zs_data['sh000001']['last_px'], 2),
                                          round(zs_data['sh000001']['change'] * 100, 2))
                # 盘面
                pm_data = chrome.fetch_data(
                    'https://x-quote.cls.cn/v2/quote/a/stock/emotion?app=CailianpressWeb&os=web&sv=8.4.6&sign=9f8797a1f4de66c2370f7a03990d2737')
                # 2.成交量
                pan.cjl = pm_data['shsz_balance'].replace('万亿', '')
                up_down_dis = pm_data['up_down_dis']
                # 3.上涨率
                szs = up_down_dis['rise_num']
                total_num = up_down_dis['rise_num'] + up_down_dis['fall_num'] + up_down_dis['flat_num']
                pan.szl = round(szs / total_num * 100, 2)
                # 4.涨停数
                pan.zts = pm_data['up_ratio_num']
                # 5.跌停数
                pan.dts = up_down_dis['down_num']
                # 6.封板率
                pan.fbl = pm_data['up_ratio']
                # 7.最高板
                ztb_data = chrome.fetch_data('https://x-quote.cls.cn/v2/quote/a/plate/up_down_analysis')
                height = ztb_data['continuous_limit_up'][0]
                pan.zgb = height['height']
                self.update_bk1_by_cls(ztb_data['plate_stock'], dtn)
                self.update_bk2_by_jys(chrome, dtn)
                # 8.每日收评
                chrome.access('https://www.cls.cn/subject/1139')
                rev_text = chrome.text('//*[@id="__next"]/div/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/a')
                if '】' in rev_text:
                    pan.review = rev_text.split('】')[1]
                # 9.最强题材
                pan.concept = self.fetch_concept(dtn)
                # 10.今日机会
                subject_data = chrome.fetch_data('https://www.cls.cn/api/subject/recommend/article?app=CailianpressWeb&os=web&sv=8.4.6&sign=9f8797a1f4de66c2370f7a03990d2737')
                chance = subject_data['today_chances']
                pan.chance = '{} | {} {}<br>{} | {} {}<br>{} | {} {}'.format(
                    chance[0]['subject_name'], chance[0]['article_name'], stock_link(chance[0]['stock_list'], 'StockID', 'name', 'last', 'RiseRange'),
                    chance[1]['subject_name'], chance[1]['article_name'], stock_link(chance[1]['stock_list'], 'StockID', 'name', 'last', 'RiseRange'),
                    chance[2]['subject_name'], chance[2]['article_name'], stock_link(chance[2]['stock_list'], 'StockID', 'name', 'last', 'RiseRange'))
                # 11.今日风口
                tuyere = subject_data['today_tuyeres']
                pan.tuyere = '{} | {} {}<br>{} | {} {}<br>{} | {} {}'.format(
                    tuyere[0]['subject_name'], tuyere[0]['driver'], stock_link(tuyere[0]['stocks'], 'StockID', 'name', 'last', 'RiseRange'),
                    tuyere[1]['subject_name'], tuyere[1]['driver'], stock_link(tuyere[1]['stocks'], 'StockID', 'name', 'last', 'RiseRange'),
                    tuyere[2]['subject_name'], tuyere[2]['driver'], stock_link(tuyere[2]['stocks'], 'StockID', 'name', 'last', 'RiseRange'))
                # 12.今日话题
                topic_url = 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/topic?page=1&page_size=10'
                topic_data = chrome.fetch_data(topic_url)['topic_list']
                pan.topic = '(1){}|{}<br>(2){}|{}<br>(3){}|{}'.format(
                    topic_data[0]['title'], topic_data[0]['description'],
                    topic_data[1]['title'], topic_data[1]['description'],
                    topic_data[2]['title'], topic_data[2]['description'],
                    topic_data[3]['title'], topic_data[3]['description'],
                    topic_data[4]['title'], topic_data[4]['description'])
                # 13.热门题材
                subject_url = 'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/plate?type=concept'
                plate_list = chrome.fetch_data(subject_url)['plate_list']
                pan.subject = '(1){}|{}<br>(2){}|{}<br>(3){}|{}'.format(
                    plate_list[0]['name'], '' if 'hot_tag' not in plate_list[0] else plate_list[0]['hot_tag'] + '' if 'tag' not in plate_list[0] else plate_list[0]['tag'],
                    plate_list[1]['name'], '' if 'hot_tag' not in plate_list[1] else plate_list[1]['hot_tag'] + '' if 'tag' not in plate_list[1] else plate_list[1]['tag'],
                    plate_list[2]['name'], '' if 'hot_tag' not in plate_list[2] else plate_list[2]['hot_tag'] + '' if 'tag' not in plate_list[2] else plate_list[2]['tag'],
                    plate_list[3]['name'], '' if 'hot_tag' not in plate_list[3] else plate_list[3]['hot_tag'] + '' if 'tag' not in plate_list[3] else plate_list[3]['tag'],
                    plate_list[4]['name'], '' if 'hot_tag' not in plate_list[4] else plate_list[4]['hot_tag'] + '' if 'tag' not in plate_list[4] else plate_list[4]['tag'])
                # 14.资金动向
                fund_data = chrome.fetch_data('https://x-quote.cls.cn/web_quote/plate/plate_list?app=CailianpressWeb&os=web&page=1&rever=1&sv=8.4.6&type=industry&way=change&sign=ef1ec7886be706a0b722d7e7bf3c0054')
                top_fund = fund_data['main_fund_diff']['top_main_fund_diff']
                last_fund = fund_data['main_fund_diff']['last_main_fund_diff']
                pan.fund = '流入 (1) {}({}亿,{}%); (2) {}({}亿,{}); (3) {}({}亿,{})<br> 流出 (1) {}({},{}); (2) {}({},{}) ; (3) {}({},{})'.format(
                    top_fund[0]['secu_name'], round(top_fund[0]['main_fund_diff'] / 100000000, 2),
                    round(top_fund[0]['change'] * 100, 2),
                    top_fund[1]['secu_name'], round(top_fund[1]['main_fund_diff'] / 100000000, 2),
                    round(top_fund[1]['change'] * 100, 2),
                    top_fund[2]['secu_name'], round(top_fund[2]['main_fund_diff'] / 100000000, 2),
                    round(top_fund[2]['change'] * 100, 2),
                    last_fund[0]['secu_name'], round(last_fund[0]['main_fund_diff'] / 100000000, 2),
                    round(last_fund[0]['change'] * 100, 2),
                    last_fund[1]['secu_name'], round(last_fund[1]['main_fund_diff'] / 100000000, 2),
                    round(last_fund[1]['change'] * 100, 2),
                    last_fund[2]['secu_name'], round(last_fund[2]['main_fund_diff'] / 100000000, 2),
                    round(last_fund[2]['change'] * 100, 2))
                # 15.短期潜伏
                latent = subject_data['short_latents']
                pan.latent = '{} | {}<br>{} | {}<br>{} | {};'.format(
                    latent[0]['subject_name'], latent[0]['subject_description'],
                    latent[1]['subject_name'], latent[1]['subject_description'],
                    latent[2]['subject_name'], latent[2]['subject_description']
                )
                pan.created = datetime.now()
                pan.save()

                # hot
                hots = []
                """ 淘股吧,24小时热股榜单 """
                hot_tgb = chrome.fetch_data("https://www.taoguba.com.cn/new/nrnt/getNoticeStock?type=D", data='dto')
                hot_cls = chrome.fetch_data('https://api3.cls.cn/v1/hot_stock?app=cailianpress&os=ios&sv=800&sign=f7f970ee36fc102317eeea2e5a6eb178')
                hot_ths = chrome.fetch_data("https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock?stock_type=a&type=day&list_type=normal")['stock_list']
                if len(hot_ths) < 10:
                    hot_ths = chrome.fetch_data(
                        "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock?stock_type=a&type=hour&list_type=normal")[
                        'stock_list']
                scores = [37, 31, 29, 23, 19, 17, 13, 11, 7, 5, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1]
                for i in range(20):
                    cls_stock = hot_cls[i]['stock']
                    up_reason = chrome.fetch_data('https://x-quote.cls.cn/v2/quote/a/stock/up_reason?app=cailianpress&os=ios&sv=800&secu_codes={}&sign=f7f970ee36fc102317eeea2e5a6eb178'.format(
                            cls_stock['StockID']))
                    cls_reason, cls_comment = '', ''
                    reason_data = up_reason[cls_stock['StockID']]
                    if 'rel_plate' in reason_data:
                        cls_reason = ', '.join([plate['plate_name'] for plate in reason_data['rel_plate']])
                    if reason_data['up_reason'] is not None:
                        cls_comment = reason_data['up_reason']
                    if not cls_stock['StockID'][2:].startswith("8"):
                        self.set_hots(hots, dtn, 'cls', (i+1), scores[i], cls_stock['StockID'][2:], cls_stock['name'], cls_reason, cls_comment)
                    ths_stock = hot_ths[i]
                    ths_reason = ",".join(ths_stock['tag']['concept_tag'])
                    ths_comment = ''
                    if 'popularity_tag' in ths_stock['tag']:
                        ths_comment = ths_stock['tag']['popularity_tag'] + '|'
                    if 'analyse_title' in ths_stock:
                        ths_comment = ths_comment + ths_stock['analyse_title']
                    if not ths_stock['code'].startswith("8"):
                        self.set_hots(hots, dtn, 'ths', (i+1), scores[i], ths_stock['code'], ths_stock['name'], ths_reason, ths_comment)
                    hot3 = hot_tgb[i]
                    tgb_reason, tgb_comment = '', ''
                    if 'reason' in hot3:
                        tgb_reason = hot3['reason']
                    if 'linkingBoard' in hot3:
                        tgb_comment = hot3['linkingBoard']
                    if 'gnList' in hot3:
                        tgb_comment = '{}{}'.format('' if tgb_comment == '' else tgb_comment + '|', ', '.join([gn['gnName'] for gn in hot3['gnList']]))
                    if not hot3['fullCode'][2:].startswith("8"):
                        self.set_hots(hots, dtn, 'tgb', (i+1), scores[i], hot3['fullCode'][2:], hot3['stockName'], tgb_reason, tgb_comment)
                top_10 = sorted(hots, key=lambda x: x.score, reverse=True)[:10]
                for top in top_10:
                    top.price, top.change = self.fetch_last_price(chrome, top.code)
                    top.created = datetime.now()
                    top.save()
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            chrome.quit()

    @staticmethod
    def set_hots(hots, dt, source, rank, score, code, name, reason, comment):
        filtered_hots = [hot for hot in hots if hot.code == code]
        if len(filtered_hots) == 0:
            hot = Hot()
            hot.date = dt
            hot.code = code
            hot.name = name
            hot.reason = reason
            hot.score = score
            hot.comment = comment
            if source == 'cls':
                hot.rank1 = rank
            elif source == 'ths':
                hot.rank2 = rank
            else:
                hot.rank3 = rank
            hots.append(hot)
        else:
            hot = filtered_hots[0]
            hot.reason = '{}; {}'.format(hot.reason, reason)
            hot.score += score
            hot.comment = '{}; {}'.format(hot.comment, comment)
            if source == 'cls':
                hot.rank1 = rank
            elif source == 'ths':
                hot.rank2 = rank
            else:
                hot.rank3 = rank

    @staticmethod
    def fetch_last_price(chrome, code):
        full_code = '{}{}'.format('sh' if code.startswith('60') or code.startswith('68') else 'sz', code)
        stock = chrome.fetch_data('https://x-quote.cls.cn/quote/stock/basic?secu_code={}&fields=change,last_px&sv=8.4.6&sign=9f8797a1f4de66c2370f7a03990d2737'.format(full_code))
        last_px, change = 0, 0
        if 'last_px' in stock:
            last_px = stock['last_px']
        if 'change' in stock:
            change = stock['change']
        if change is None or last_px is None:
            change = 0
        return last_px, '{}%'.format(round(change * 100, 2))

    @staticmethod
    def update_bk1_by_cls(plate_stock, dtn):
        for ps in plate_stock:
            bk_name = ps['secu_name']
            for stock in ps['stock_list']:
                if 'ST' not in bk_name:
                    zt = Ztb()
                    zt.date = dtn
                    zt.code = stock['secu_code'][2:]
                    zt.name = stock['secu_name']
                    zt.bk1 = bk_name
                    zt.bk2 = ''
                    zt.change = stock['change']
                    zt.price = stock['last_px']
                    ztt = stock['time'].split(' ')
                    zt.time = ztt[1]
                    zt.strong = stock['up_num']
                    up_reason = stock['up_reason'].split('|')
                    zt.reason = up_reason[0]
                    zt.comment1 = up_reason[1]
                    zt.comment2 = ''
                    zt.created = datetime.now()
                    zt.save()

    @staticmethod
    def update_bk2_by_jys(chrome, dtn):
        """ 韭研社，每日涨停 """
        chrome.access('https://www.jiuyangongshe.com/action')
        chrome.click('//div[@class="active"]')
        chrome.click('//div[@id="tab-accounts"]')
        chrome.input('//div[@id="pane-accounts"]//input[@name="phone"]', '13631367271')
        chrome.input('//div[@id="pane-accounts"]//input[@name="password"]', 'hsy841121')
        chrome.click('//div[@id="pane-accounts"]//button[@type="button"]')
        time.sleep(3)
        chrome.click('//div[text()="全部异动解析"]', timeout=10)
        time.sleep(3)
        modules = chrome.elements("//section/ul/li")
        for module in modules:
            bk = chrome.element(".//div[contains(@class, 'parent')]/div[1]", parent=module)
            if bk and not bk.text.__contains__('ST'):
                lis = module.find_elements(By.TAG_NAME, 'li')
                for li in lis:
                    shrinks = li.find_elements(By.XPATH, ".//div[contains(@class, 'shrink')]")
                    code = shrinks[1].get_attribute("innerText")[2:]
                    zts_comment = li.find_element(By.XPATH, ".//pre[contains(@class, 'expound')]/a").get_attribute("innerText").split('\n')
                    ztb = Ztb.select().where(Ztb.date == dtn and Ztb.code == code)
                    for zt in ztb:
                        zt.reason = '{} | {}'.format(zt.reason, zts_comment[0])
                        zt.bk2 = bk.text
                        zt.comment2 = zts_comment[1]
                        zt.save()

    @staticmethod
    def fetch_concept(dtn):
        bk1 = (Ztb.select(Ztb.bk1, fn.COUNT(1).alias('size'))
               .where(Ztb.date == dtn)
               .group_by(Ztb.bk1)
               .order_by(fn.COUNT(1).desc()))
        bk2 = (Ztb.select(Ztb.bk2, fn.COUNT(1).alias('size'))
               .where(Ztb.date == dtn)
               .group_by(Ztb.bk2)
               .order_by(fn.COUNT(1).desc()))
        concept = ''
        idx = 0
        for bk in bk1:
            if bk.bk1 != '其他' and 'ST' not in bk.bk1:
                concept = '{}{}({})'.format(concept if concept == '' else concept + '|', bk.bk1, bk.size)
                idx = idx + 1
                if idx > 1:
                    break
        idx = 0
        for bk in bk2:
            if bk.bk2 != '其他' and 'ST' not in bk.bk2:
                concept = '{}{}({})'.format(concept if concept == '' else concept + '|', bk.bk2, bk.size)
                idx = idx + 1
                if idx > 1:
                    break
        return concept


def set_hots2(hots, dt, source, rank, score, code, name, reason, comment):
    filtered_hots = [hot for hot in hots if hot.code == code]
    if len(filtered_hots) == 0:
        hot = Hot()
        hot.date = dt
        hot.code = code
        hot.name = name
        hot.reason = reason
        hot.score = score
        hot.comment = comment
        if source == 'cls':
            hot.rank1 = rank
        elif source == 'ths':
            hot.rank2 = rank
        else:
            hot.rank3 = rank
        hots.append(hot)
    else:
        hot = filtered_hots[0]
        hot.reason = '{}; {}'.format(hot.reason, reason)
        hot.score += score
        hot.comment = '{}; {}'.format(hot.comment, comment)
        if source == 'cls':
            hot.rank1 = rank
        elif source == 'ths':
            hot.rank2 = rank
        else:
            hot.rank3 = rank


if __name__ == '__main__':
    fupan = engines.engine.engines['fupan']()
    fupan.fetch()





