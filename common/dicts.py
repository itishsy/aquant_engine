
def freq_level(ts=None):
    if ts is None:
        return [(0, [15, 30, 60]), (1, [5, 10, 15]), (2, [5, 10, 15, 30, 60]), (3, [101]), (4, [])]
    if ts == 0:
        return [15, 30, 60]
    if ts == 1:
        return [5, 10, 15]
    if ts == 2:
        return [5, 10, 15, 30, 60]
    if ts == 3:
        return [101]
    if ts == 4:
        return []
    return [5, 10, 15, 30, 60, 120, 101]


def choice_strategy(key=None):
    if key is None:
        return [('UAR', 'UAR'), ('DRC', 'DRC'), ('PAB', 'PAB'), ('HOT', 'HOT')]
    if key == 'UAR':
        return 'UAR'
    if key == 'DRC':
        return 'DRC'
    if key == 'PAB':
        return 'PAB'
    if key == 'HOT':
        return 'HOT'
    return 'undefined'


def choice_source(key=None):
    if key is None:
        return [('ENGINE', 'ENGINE'), ('HOT', 'HOT')]
    if key == 'ENGINE':
        return 'ENGINE'
    if key == 'MANUAL':
        return 'MANUAL'
    return 'undefined'


def choice_status(key=None):
    if key is None:
        return [(0, '失效'), (1, '有效')]
    if key == 0:
        return '失效'
    if key == 1:
        return '有效'
    return 'undefined'


def watch_freq(key=None):
    if key is None:
        return [(0, [15, 30, 60]), (1, [5, 10, 15]), (2, [5, 10, 15, 30, 60]), (3, [60, 120, 101]),
                (4, [60, 120, 101, 102])]
    if key == 0:
        return [15, 30, 60]
    if key == 1:
        return [5, 10, 15]
    if key == 2:
        return [5, 10, 15, 30, 60]
    if key == 3:
        return [60, 120, 101]
    if key == 4:
        return [60, 120, 101, 102]
    return []


def trade_type(key=None):
    if key is None:
        return [(0, '买入'), (1, '卖出')]
    if key == 0:
        return '买入'
    if key == 1:
        return '卖出'
    return 'undefined'


def trade_comment(key=None):
    if key is None:
        return [('开仓', '开仓'), ('减仓', '减仓'), ('加仓', '加仓'), ('平仓', '平仓'), ('止损', '止损'),
                ('止盈', '止盈')]
    if key == '开仓':
        return '开仓'
    if key == '减仓':
        return '减仓'
    if key == '加仓':
        return '加仓'
    if key == '平仓':
        return '平仓'
    if key == '止损':
        return '止损'
    if key == '止盈':
        return '止盈'
    return 'undefined'


def trade_strategy(key=None):
    if key is None:
        return [('UAB', '趋势调整'), ('PAB', '平台调整'), ('PBC', '平台突破'), ('DRC', '底部反转')]
    if key == 'UAB':
        return '趋势调整'
    if key == 'PAB':
        return '平台调整'
    if key == 'PBC':
        return '平台突破'
    if key == 'DRC':
        return '底部反转'
    return 'undefined'


def buy_type(key=None):
    if key is None:
        return [('R60C15', 'R60C15'), ('R30C5', 'R30C5'), ('R60C10', 'R60C10'), ('R15C1', 'R15C1'),
                ('R101C30', 'R101C30'), ('ARC', 'ARC')]
    if key == 'R60C15':
        return 'R60C15'
    if key == 'R30C5':
        return 'R30C5'
    if key == 'R60C10':
        return 'R60C10'
    if key == 'R15C1':
        return 'R15C1'
    if key == 'R101C30':
        return 'R101C30'
    if key == 'ARC':
        return 'ARC'
    return 'undefined'


def valid_status(key=None):
    if key is None:
        return [(0, '无效'), (1, '有效')]
    if key == 0:
        return '无效'
    if key == 1:
        return '有效'
    return 'undefined'


def single_source(key=None):
    if key is None:
        return [(0, '背离'), (1, '背驰'), (2, '量价背离'), (3, '分型'), (4, '量能')]
    if key == 0:
        return '背离'
    if key == 1:
        return '背驰'
    if key == 2:
        return '量价背离'
    if key == 3:
        return '分型'
    if key == 4:
        return '量能'
    return 'undefined'


def single_status(key=None):
    if key is None:
        return [(0, 'New'), (1, 'Choice'), (2, 'Unused'), (3, 'Invalid')]
    if key == 0:
        return 'New'
    if key == 1:
        return 'Choice'
    if key == 2:
        return 'Unused'
    if key == 3:
        return 'Invalid'
    return 'undefined'

