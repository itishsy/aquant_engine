import datetime

from engines.engine import Sender, job_engine, engines
from models.signal import Signal
from models.review import Pan, Hot, Ztb
from components.notify import email, stock_link


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
class Notify(Sender):

    def send(self):
        sis = Signal.select().where(Signal.notify == 0)
        if sis:
            signal_content = self._signal_content(sis)
            if email('Signal', signal_content):
                for si in sis:
                    si.notify = 1
                    si.updated = datetime.datetime.now()
                    si.save()

        pan = Pan.select().order_by(Pan.created.desc()).limit(1).get()
        if not pan.notify or pan.notify != 1:
            pan_content = self._pan_content(pan)
            if email('Review', pan_content):
                pan.notify = 1
                pan.save()

    @staticmethod
    def _signal_content(sis):
        msg = ''
        for si in sis:
            msg = msg + "{},{},{} <br>".format(stock_link(si.code, si.name), si.dt, si.strategy)
        if msg != '':
            return msg

    @staticmethod
    def _pan_content(pan):
        pan_content = "<h3>【{}】</h3> <table border='0'><tr><th style='width: 40%;'></th><th style='width: 60%;'></th>".format(
            pan.date)
        pan_content += "<tr><td>成交量</td><td>{}</td></tr>".format(pan.cjl)
        pan_content += "<tr><td>上涨率</td><td>{}，{}%</td></tr>".format(pan.zs, pan.szl)
        pan_content += "<tr><td>涨跌停</td><td>{} / {}</td></tr>".format(pan.zts, pan.dts)
        pan_content += "<tr><td>封板率</td><td>{}</td></tr>".format(pan.fbl)
        pan_content += "<tr><td>最高板</td><td>{}</td></tr>".format(pan.zgb)
        pan_content += "<tr><td>最强板块</td><td>{}</td></tr>".format(pan.concept)
        pan_content += "<tr><td>收评</td><td>{}</td></tr>".format(pan.review)
        pan_content += "<tr><td colspan='2'><h4>今日机会</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(
            pan.chance)
        pan_content += "<tr><td colspan='2'><h4>风口</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(
            pan.tuyere)
        pan_content += "<tr><td colspan='2'><h4>热门主题</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(
            pan.subject)
        pan_content += "<tr><td colspan='2'><h4>资金流向</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(
            pan.fund)
        pan_content += "<tr><td colspan='2'><h4>潜伏</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(
            pan.latent)
        pan_content += "<tr><td colspan='2'><h4>热门话题</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(
            pan.topic)
        pan_content += "</table>"

        hots = Hot.select().where(Hot.date == pan.date).order_by(Hot.score.desc())
        hot_content = "<table border='0'><tr><th style='width: 40%;'>热股</th><th style='width: 60%;'>备注</th></tr>"
        idx = 1
        for hot in hots:
            rank_str = ''
            if hot.rank1:
                rank_str += '{}({})'.format('cls', hot.rank1)
            if hot.rank2:
                rank_str += '{}({})'.format('ths', hot.rank2)
            if hot.rank3:
                rank_str += '{}({})'.format('tgb', hot.rank3)
            hot_content += "<tr><td>({}){}<br>{}</td><td>{}<br>{}</td></tr>".format(
                idx, xueqiu_link(hot.code, hot.name, hot.price, hot.change),
                hot.score, rank_str, hot.reason)
            idx = idx + 1
        hot_content += "</table>"

        ztb = Ztb.select().where(Ztb.date == pan.date).order_by(Ztb.time)
        ztb_content = "<table border='0'><tr><th style='width: 40%;'>涨停板</th><th style='width: 60%;'>原因</th></tr>"
        for zt in ztb:
            ztb_content += "<tr><td>{}<br>{}<br>{}</td><td><b>{}|{}</b><br>{}</td></tr>".format(
                xueqiu_link(zt.code, zt.name, zt.price), zt.time, zt.strong, zt.bk1, zt.bk2, zt.reason)
        ztb_content += "</table>"

        html_content = "<html>{} </br> {} </br> {}</html>".format(pan_content, hot_content, ztb_content)
        return html_content


if __name__ == '__main__':
    notify = engines['notify']()
    notify.send()
