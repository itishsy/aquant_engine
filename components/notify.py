import datetime

from models.symbol import Symbol
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def stock_link(code, name):

    if Symbol.select().where(Symbol.code == code).exists():
        sym = Symbol.select().where(Symbol.code == code).limit(1).get()
    else:
        sym = Symbol(price=0, zdf=0)
    full_code = f'SH{code}' if code.startswith('60') else f'SZ{code}'
    return "<a href='http://xueqiu.com/S/{}'>{}</a>({},{}%)".format(full_code, name, sym.price, sym.zdf)


def stock_link_by_name(name):
    if name is not None:
        name = name.split('|')[0].replace(' ', '')
        ss = Symbol.select().where(Symbol.name == name or Symbol.code == name)
        if len(ss) > 0:
            return '{}({},{})'.format(stock_link(ss[0].code, ss[0].name), ss[0].price, ss[0].zdf)
    return ''


def stock_link_by_str(name):
    ss = name.split(')')
    res = ''
    for s in ss:
        n = s.split('(')[0]
        sn = stock_link_by_name(n)
        if sn:
            res += '{}({}) '.format(sn, s.split('(')[1])
        elif s != '':
            res += '{}) '.format(s)
    return res


def email(subject, body):
    try:
        smtp_server = "smtp.163.com"
        smtp_username = "itishsy@163.com"
        smtp_password = "KSEJTXDLZLXNBMMI"
        smtp = smtplib.SMTP(smtp_server, port=25)
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        from_email = "itishsy@163.com"
        to_email = "279440948@qq.com"
        message = MIMEMultipart()
        message["From"] = "itishsy@163.com"
        message["To"] = "279440948@qq.com"
        message["Subject"] = subject
        message.attach(MIMEText(body, "html", "utf-8"))
        # subject = subject
        # body = body.encode('utf-8')
        # message = f"From: {from_email}\nTo: {to_email}\nSubject: {subject}\n\n{body}"
        smtp.sendmail(from_email, to_email, message.as_string())
        smtp.quit()
        return True
    except Exception as e:
        traceback.print_exc()
        return False


def signal_notify(sis):
    msg = ''
    for si in sis:
        msg = msg + "{},{},{},{} <br>".format(stock_link(si.code, si.name), si.dt, si.stage, si.strategy)
    if msg != '':
        return msg


def review_notify():
    reviews = Review.select().order_by(Review.created.desc()).limit(1)
    review = reviews[0]
    zt_str, ztd_str = '', ''
    for p in reviews:
        zt_str = zt_str + ',' + p.zt
        ztd_str = ztd_str + ',' + p.ztd
    ztt = '一板{},二板{},三板{},高板{}'.format(review.zt1,review.zt2,review.zt3,review.zth)

    pan_content = "<h3>【{}】</h3> <table border='0'><tr><th style='width: 30%;'></th><th style='width: 70%;'></th>".format(review.date)
    pan_content += "<tr><td>成交量</td><td>{}</td></tr>".format(review.cjl)
    pan_content += "<tr><td>指数</td><td>{}</td></tr>".format(review.zs)
    pan_content += "<tr><td>上涨数</td><td>{}</td></tr>".format(review.szs)
    pan_content += "<tr><td>涨停数</td><td>{}({})</td></tr>".format(review.zt, zt_str[1:])
    pan_content += "<tr><td>最高板</td><td>{} ({})</td></tr>".format(review.zth, ztd_str[1:])
    pan_content += "<tr><td>涨停梯度</td><td>{}</td></tr>".format(ztt)
    pan_content += "<tr><td colspan='2'><h4>资金流向</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(review.fund)
    pan_content += "<tr><td colspan='2'><h4>今日主题</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(review.subject)
    pan_content += "<tr><td colspan='2'><h4>风口</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(review.tuyere)
    pan_content += "<tr><td colspan='2'><h4>潜伏</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(review.latent)
    pan_content += "<tr><td colspan='2'><h4>热门话题</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(review.topic)
    pan_content += "<tr><td colspan='2'><h4>热门题材</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(review.concept)
    pan_content += "<tr><td colspan='2'><h4>长线机会</h4></td></tr><tr><td colspan='2'>{}</td></tr>".format(review.chance)
    pan_content += "</table>"

    hots = Hot.select().where(Hot.bk == 'hot', Hot.date == datetime.datetime.now().strftime("%Y-%m-%d")).order_by(Hot.source, Hot.rank)
    hot_content = "<table border='0'><tr><th style='width: 30%;'>热股</th><th style='width: 70%;'>备注</th></tr>"
    for hot in hots:
        hot_content += "<tr><td>({}){}</td><td>{}\n{}\n{}</td></tr>".format(hot.rank, xueqiu_link(hot.code, hot.name),
                                                                            hot.comment, hot.comment2, hot.comment3)
    hot_content += "</table>"

    zts = Hot.select().where(Hot.source == 'zt', Hot.date == datetime.datetime.now().strftime("%Y-%m-%d")).order_by(Hot.rank)
    ztb_content = "<table border='0'><tr><th style='width: 35%;'>涨停板</th><th style='width: 65%;'>原因</th></tr>"
    for zt in zts:
        ztb_content += "<tr><td>{}({}B)({},{})</td><td>{}{}。</td></tr>".format(stock_link(zt.code, zt.name), zt.rank,
                                                                               zt.ztt, zt.bk, zt.comment, zt.comment2)
    ztb_content += "</table>"

    html_content = "<html>{} </br> {} </br> {}</html>".format(pan_content, hot_content, ztb_content)
    return html_content

