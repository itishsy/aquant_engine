from collections import Counter
from datetime import datetime
import time
import traceback

import requests
from bs4 import BeautifulSoup

from engines.engine import Fetcher, job_engine
from components.chrome_driver import ChromeDriver, By
from models.base import db
from models.review import Pan, Hot, Ztb


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
    return "<a href='http://xueqiu.com/S/SZ{}'>{}{}</a> ".format(code, name, block)


@job_engine
class Fupan(Fetcher):
    HOT_SCORES = [37, 31, 29, 23, 19, 17, 13, 11, 7, 5, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/147.0.7727.57 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        })

    def fetch(self):
        try:
            dtn = datetime.now().strftime("%Y-%m-%d")
            pan_data = self._build_pan_data(dtn)
            ztb_rows = self._fetch_cls_ztb_rows(dtn, pan_data)
            self._fill_jys_ztb(ztb_rows, dtn)
            pan_data['concept'] = self._build_concept(ztb_rows)
            hot_rows = self._build_hot_rows(dtn)
            self._save_all(dtn, pan_data, ztb_rows, hot_rows)
        except Exception as ex:
            print(ex)
            traceback.print_exc()

    def _get_json(self, url, data_key='data', referer=None, retries=3):
        headers = {}
        if referer:
            headers["Referer"] = referer
        last_error = None
        for idx in range(retries):
            try:
                response = self.session.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                payload = response.json()
                return payload[data_key]
            except Exception as ex:
                last_error = ex
                time.sleep(1 + idx)
        raise last_error

    def _get_html(self, url, referer=None, retries=3):
        headers = {}
        if referer:
            headers["Referer"] = referer
        last_error = None
        for idx in range(retries):
            try:
                response = self.session.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                return response.text
            except Exception as ex:
                last_error = ex
                time.sleep(1 + idx)
        raise last_error

    def _build_pan_data(self, dtn):
        pan = {
            'date': dtn,
            'cjl': '',
            'zs': '',
            'szl': '',
            'zts': '',
            'dts': '',
            'fbl': '',
            'zgb': '',
            'review': '',
            'concept': '',
            'chance': '',
            'tuyere': '',
            'topic': '',
            'subject': '',
            'fund': '',
            'latent': '',
        }

        zs_data = self._get_json(
            'https://x-quote.cls.cn/v2/quote/a/web/stocks/basic?app=CailianpressWeb&fields=secu_name,secu_code,trade_status,change,change_px,last_px&os=web&secu_codes=sh000001,sz399001,sh000905,sz399006&sv=8.4.6&sign=7ddfd2eef7564087ff01a1782c724f43',
            referer='https://www.cls.cn/',
        )
        pan['zs'] = '{}({}%)'.format(
            round(zs_data['sh000001']['last_px'], 2),
            round(zs_data['sh000001']['change'] * 100, 2),
        )

        pm_data = self._get_json(
            'https://x-quote.cls.cn/v2/quote/a/stock/emotion?app=CailianpressWeb&os=web&sv=8.4.6&sign=9f8797a1f4de66c2370f7a03990d2737',
            referer='https://www.cls.cn/',
        )
        pan['cjl'] = pm_data['shsz_balance'].replace('万亿', '')
        up_down_dis = pm_data['up_down_dis']
        total_num = up_down_dis['rise_num'] + up_down_dis['fall_num'] + up_down_dis['flat_num']
        pan['szl'] = round(up_down_dis['rise_num'] / total_num * 100, 2) if total_num else 0
        pan['zts'] = pm_data['up_ratio_num']
        pan['dts'] = up_down_dis['down_num']
        pan['fbl'] = pm_data['up_ratio']

        subject_data = self._get_json(
            'https://www.cls.cn/api/subject/recommend/article?app=CailianpressWeb&os=web&sv=8.4.6&sign=9f8797a1f4de66c2370f7a03990d2737',
            referer='https://www.cls.cn/',
        )
        pan['chance'] = self._format_subject_items(subject_data.get('today_chances', []), 'stock_list', 'article_name')
        pan['tuyere'] = self._format_subject_items(subject_data.get('today_tuyeres', []), 'stocks', 'driver')
        pan['latent'] = self._format_latent(subject_data.get('short_latents', []))

        topic_data = self._get_json(
            'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/topic?page=1&page_size=10',
            referer='https://dq.10jqka.com.cn/',
        )
        pan['topic'] = self._format_ranked_text(topic_data.get('topic_list', []), 'title', 'description')

        plate_data = self._get_json(
            'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/plate?type=concept',
            referer='https://dq.10jqka.com.cn/',
        )
        pan['subject'] = self._format_plate_list(plate_data.get('plate_list', []))

        fund_data = self._get_json(
            'https://x-quote.cls.cn/web_quote/plate/plate_list?app=CailianpressWeb&os=web&page=1&rever=1&sv=8.4.6&type=industry&way=change&sign=ef1ec7886be706a0b722d7e7bf3c0054',
            referer='https://www.cls.cn/',
        )
        pan['fund'] = self._format_fund(fund_data.get('main_fund_diff', {}))
        pan['review'] = self._fetch_review_text()
        return pan

    def _fetch_review_text(self):
        html = self._get_html('https://api3.cls.cn/share/subject/1139', referer='https://api3.cls.cn/')
        soup = BeautifulSoup(html, 'html.parser')
        for span in soup.select('#mescroll0 li div a span'):
            text = span.get_text(strip=True)
            if '每日收评' in text:
                if '】' in text:
                    return text.split('】', 1)[1]
                return text.replace('每日收评', '').strip('【】 :：')
        return ''

    def _fetch_cls_ztb_rows(self, dtn, pan_data):
        ztb_data = self._get_json(
            'https://x-quote.cls.cn/v2/quote/a/plate/up_down_analysis',
            referer='https://www.cls.cn/',
        )
        continuous = ztb_data.get('continuous_limit_up', [])
        pan_data['zgb'] = continuous[0]['height'] if continuous else ''
        rows = []
        for plate in ztb_data.get('plate_stock', []):
            bk_name = plate['secu_name']
            if 'ST' in bk_name:
                continue
            for stock in plate.get('stock_list', []):
                row = Ztb()
                row.date = dtn
                row.code = stock['secu_code'][2:]
                row.name = stock['secu_name']
                row.change = stock['change']
                row.time = stock['time'].split(' ')[1]
                row.price = stock['last_px']
                row.strong = stock.get('up_num')
                row.bk1 = bk_name
                row.bk2 = ''
                up_reason = (stock.get('up_reason') or '').split('|', 1)
                row.reason = up_reason[0] if up_reason else ''
                row.comment1 = up_reason[1] if len(up_reason) > 1 else ''
                row.comment2 = ''
                row.created = datetime.now()
                rows.append(row)
        return rows

    def _fill_jys_ztb(self, ztb_rows, dtn):
        by_code = {}
        for row in ztb_rows:
            by_code.setdefault(row.code, []).append(row)

        chrome = ChromeDriver()
        try:
            if chrome.driver is None:
                return
            chrome.access('https://www.jiuyangongshe.com/action')
            chrome.click('//div[@class="active"]')
            chrome.click('//div[@id="tab-accounts"]')
            chrome.input('//div[@id="pane-accounts"]//input[@name="phone"]', '13631367271')
            chrome.input('//div[@id="pane-accounts"]//input[@name="password"]', 'hsy841121')
            chrome.click('//div[@id="pane-accounts"]//button[@type="button"]')
            time.sleep(3)
            chrome.click('//div[text()="全部异动解析"]', timeout=10)
            time.sleep(3)
            modules = chrome.elements("//section/ul/li") or []
            for module in modules:
                bk = chrome.element(".//div[contains(@class, 'parent')]/div[1]", parent=module)
                if bk is None or 'ST' in bk.text:
                    continue
                lis = module.find_elements(By.TAG_NAME, 'li')
                for li in lis:
                    shrinks = li.find_elements(By.XPATH, ".//div[contains(@class, 'shrink')]")
                    if len(shrinks) < 2:
                        continue
                    code = shrinks[1].get_attribute("innerText")[2:]
                    comments = li.find_element(By.XPATH, ".//pre[contains(@class, 'expound')]/a").get_attribute("innerText").split('\n')
                    for row in by_code.get(code, []):
                        row.reason = '{} | {}'.format(row.reason, comments[0]) if row.reason else comments[0]
                        row.bk2 = bk.text
                        row.comment2 = comments[1] if len(comments) > 1 else ''
        except Exception as ex:
            print('update_bk2_by_jys skipped:', ex)
        finally:
            chrome.quit()

    def _build_hot_rows(self, dtn):
        hots = []
        hot_cls = self._get_json(
            'https://api3.cls.cn/v1/hot_stock?app=cailianpress&os=ios&sv=800&sign=f7f970ee36fc102317eeea2e5a6eb178',
            referer='https://www.cls.cn/',
        )
        hot_ths = self._get_json(
            'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock?stock_type=a&type=day&list_type=normal',
            referer='https://dq.10jqka.com.cn/',
        ).get('stock_list', [])
        if len(hot_ths) < 10:
            hot_ths = self._get_json(
                'https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock?stock_type=a&type=hour&list_type=normal',
                referer='https://dq.10jqka.com.cn/',
            ).get('stock_list', [])
        hot_tgb = self._get_json(
            'https://www.taoguba.com.cn/new/nrnt/getNoticeStock?type=D',
            data_key='dto',
            referer='https://www.taoguba.com.cn/',
        )

        for idx, item in enumerate(hot_cls[:len(self.HOT_SCORES)]):
            stock = item.get('stock', {})
            stock_id = stock.get('StockID', '')
            if len(stock_id) < 3 or stock_id[2:].startswith('8'):
                continue
            reason_data = self._get_json(
                'https://x-quote.cls.cn/v2/quote/a/stock/up_reason?app=cailianpress&os=ios&sv=800&secu_codes={}&sign=f7f970ee36fc102317eeea2e5a6eb178'.format(stock_id),
                referer='https://www.cls.cn/',
            ).get(stock_id, {})
            cls_reason = ', '.join([plate['plate_name'] for plate in reason_data.get('rel_plate', [])])
            cls_comment = reason_data.get('up_reason') or ''
            self._set_hot(hots, dtn, 'cls', idx + 1, self.HOT_SCORES[idx], stock_id[2:], stock.get('name', ''), cls_reason, cls_comment)

        for idx, item in enumerate(hot_ths[:len(self.HOT_SCORES)]):
            code = item.get('code', '')
            if not code or code.startswith('8'):
                continue
            tag = item.get('tag', {})
            reason = ','.join(tag.get('concept_tag', []))
            comment = ''
            if 'popularity_tag' in tag:
                comment = tag['popularity_tag'] + '|'
            if 'analyse_title' in item:
                comment = comment + item['analyse_title']
            self._set_hot(hots, dtn, 'ths', idx + 1, self.HOT_SCORES[idx], code, item.get('name', ''), reason, comment)

        for idx, item in enumerate(hot_tgb[:len(self.HOT_SCORES)]):
            full_code = item.get('fullCode', '')
            if len(full_code) < 3 or full_code[2:].startswith('8'):
                continue
            comment = item.get('linkingBoard') or ''
            if 'gnList' in item:
                concept_names = ', '.join([gn['gnName'] for gn in item['gnList']])
                comment = '{}{}'.format('' if comment == '' else comment + '|', concept_names)
            self._set_hot(hots, dtn, 'tgb', idx + 1, self.HOT_SCORES[idx], full_code[2:], item.get('stockName', ''), item.get('reason') or '', comment)

        top_10 = sorted(hots, key=lambda item: item.score, reverse=True)[:10]
        for hot in top_10:
            hot.price, hot.change = self._fetch_last_price(hot.code)
            hot.created = datetime.now()
        return top_10

    def _fetch_last_price(self, code):
        full_code = '{}{}'.format('sh' if code.startswith('60') or code.startswith('68') else 'sz', code)
        stock = self._get_json(
            'https://x-quote.cls.cn/quote/stock/basic?secu_code={}&fields=change,last_px&sv=8.4.6&sign=9f8797a1f4de66c2370f7a03990d2737'.format(full_code),
            referer='https://www.cls.cn/',
        )
        last_px = stock.get('last_px') or 0
        change = stock.get('change') or 0
        return last_px, '{}%'.format(round(change * 100, 2))

    @staticmethod
    def _set_hot(hots, dt, source, rank, score, code, name, reason, comment):
        filtered = [hot for hot in hots if hot.code == code]
        if not filtered:
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
            return

        hot = filtered[0]
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
    def _format_subject_items(items, stocks_key, detail_key):
        if not items:
            return ''
        lines = []
        for item in items[:3]:
            lines.append(
                '{} | {} {}'.format(
                    item.get('subject_name', ''),
                    item.get(detail_key, ''),
                    stock_link(item.get(stocks_key, []), 'StockID', 'name', 'last', 'RiseRange'),
                ).strip()
            )
        return '<br>'.join(lines)

    @staticmethod
    def _format_ranked_text(items, title_key, desc_key):
        if not items:
            return ''
        lines = []
        for idx, item in enumerate(items[:5], start=1):
            lines.append('({}){}|{}'.format(idx, item.get(title_key, ''), item.get(desc_key, '')))
        return '<br>'.join(lines)

    @staticmethod
    def _format_plate_list(plate_list):
        if not plate_list:
            return ''
        lines = []
        for idx, plate in enumerate(plate_list[:5], start=1):
            tag = plate.get('hot_tag') or plate.get('tag') or ''
            lines.append('({}){}|{}'.format(idx, plate.get('name', ''), tag))
        return '<br>'.join(lines)

    @staticmethod
    def _format_fund(main_fund):
        top_fund = main_fund.get('top_main_fund_diff', [])
        last_fund = main_fund.get('last_main_fund_diff', [])
        if len(top_fund) < 3 or len(last_fund) < 3:
            return ''
        return '流入 (1) {}({}亿,{}%); (2) {}({}亿,{}%); (3) {}({}亿,{}%)<br> 流出 (1) {}({}亿,{}%); (2) {}({}亿,{}%); (3) {}({}亿,{}%)'.format(
            top_fund[0]['secu_name'], round(top_fund[0]['main_fund_diff'] / 100000000, 2), round(top_fund[0]['change'] * 100, 2),
            top_fund[1]['secu_name'], round(top_fund[1]['main_fund_diff'] / 100000000, 2), round(top_fund[1]['change'] * 100, 2),
            top_fund[2]['secu_name'], round(top_fund[2]['main_fund_diff'] / 100000000, 2), round(top_fund[2]['change'] * 100, 2),
            last_fund[0]['secu_name'], round(last_fund[0]['main_fund_diff'] / 100000000, 2), round(last_fund[0]['change'] * 100, 2),
            last_fund[1]['secu_name'], round(last_fund[1]['main_fund_diff'] / 100000000, 2), round(last_fund[1]['change'] * 100, 2),
            last_fund[2]['secu_name'], round(last_fund[2]['main_fund_diff'] / 100000000, 2), round(last_fund[2]['change'] * 100, 2),
        )

    @staticmethod
    def _format_latent(latent):
        return '{} | {}<br>{} | {}<br>{} | {};'.format(
            latent[0]['subject_name'] if len(latent) > 0 else '', latent[0]['subject_description'] if len(latent) > 0 else '',
            latent[1]['subject_name'] if len(latent) > 1 else '', latent[1]['subject_description'] if len(latent) > 1 else '',
            latent[2]['subject_name'] if len(latent) > 2 else '', latent[2]['subject_description'] if len(latent) > 2 else '',
        )

    @staticmethod
    def _build_concept(ztb_rows):
        counter1 = Counter()
        counter2 = Counter()
        for row in ztb_rows:
            if row.bk1 and row.bk1 != '其他' and 'ST' not in row.bk1:
                counter1[row.bk1] += 1
            if row.bk2 and row.bk2 != '其他' and 'ST' not in row.bk2:
                counter2[row.bk2] += 1

        items = []
        for name, size in counter1.most_common(2):
            items.append('{}({})'.format(name, size))
        for name, size in counter2.most_common(2):
            items.append('{}({})'.format(name, size))
        return '|'.join(items)

    def _save_all(self, dtn, pan_data, ztb_rows, hot_rows):
        with db.atomic():
            Hot.delete().where(Hot.date == dtn).execute()
            Ztb.delete().where(Ztb.date == dtn).execute()

            pan = Pan.select().where(Pan.date == dtn).order_by(Pan.id.desc()).first()
            if pan is None:
                pan = Pan()
            else:
                Pan.delete().where((Pan.date == dtn) & (Pan.id != pan.id)).execute()

            pan.date = dtn
            pan.cjl = pan_data['cjl']
            pan.zs = pan_data['zs']
            pan.szl = pan_data['szl']
            pan.zts = pan_data['zts']
            pan.dts = pan_data['dts']
            pan.fbl = pan_data['fbl']
            pan.zgb = pan_data['zgb']
            pan.review = pan_data['review']
            pan.concept = pan_data['concept']
            pan.chance = pan_data['chance']
            pan.tuyere = pan_data['tuyere']
            pan.topic = pan_data['topic']
            pan.subject = pan_data['subject']
            pan.fund = pan_data['fund']
            pan.latent = pan_data['latent']
            pan.created = datetime.now()
            pan.save()

            for row in ztb_rows:
                row.save()
            for row in hot_rows:
                row.save()
