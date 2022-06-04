import asyncio
import functions_framework
import datetime as dt
from flask import abort

import pybotters  # pip install pybotters
import json

import environment as env
from line_utility import line_utility
from google_utility import google_utility
import html_utility


def get_strategy(setting: dict, strategy_name: str):

    strateges = setting.get('strateges')

    for i in range(len(strateges)):
        if strateges[i].get('strategy_name', '').lower() == strategy_name.lower():
            strategy: dict = strateges[i]
            return strategy
        pass

    return None


def get_exchange(setting: dict, exchange: str):

    exchanges = setting.get('exchanges')

    for i in range(len(exchanges)):
        if exchanges[i].get('exchange', '').lower() == exchange.lower():
            exchange: dict = exchanges[i]
            return exchange
        pass

    return None


def get_position(history_data: str):

    histories = history_data.splitlines()
    is_first = True
    position = 0

    for history in histories:
        if is_first:
            # 先頭はヘッダー行のため、飛ばす
            is_first = False
            continue
        data = history.split(',')
        position = position + (float(data[5]) * (1 if data[2] == 'BUY' else -1))
        pass

    return position


async def binance_order_main(strategy_name: str, trade_category: str, setting: dict):

    line = line_utility(setting['line'])

    # 売買区分が想定通りか
    if 'sell' != trade_category and 'buy' != trade_category and 'close_all' != trade_category:
        print('trade category does not match.')
        messages = line.get_messages_text(f'{strategy_name}: trade category does not match.')
        await line.broadcast_send(messages, True)
        return abort(500)

    # ストラテジー取得
    target_strategy = get_strategy(setting, strategy_name)
    quantity = target_strategy.get('quantity')
    exchange = target_strategy.get('exchange')
    symbol = target_strategy.get('symbol')

    # APIキー確認
    target_exchange = get_exchange(setting, exchange)
    if target_exchange is None or target_exchange.get('api_key', '') == '' or target_exchange.get('api_secret', '') == '':
        print("API key or secret key has not been set.")
        messages = line.get_messages_text(f'{strategy_name}: API key or secret key has not been set.')
        await line.broadcast_send(messages, True)
        return abort(500)

    apis = {}
    base_url = ''

    # testnet確認
    if 'testnet' in exchange:
        apis = {"binance_testnet": [target_exchange.get('api_key', ''), target_exchange.get('api_secret', '')]}
        base_url = 'https://testnet.binancefuture.com'
        pass
    else:
        apis = {"binance": [target_exchange.get('api_key', ''), target_exchange.get('api_secret', '')]}
        base_url = 'https://fapi.binance.com'
        pass

    print(base_url)

    google = None
    if __name__ == '__main__':
        # デバッグ用
        google_strategy = {
            "strategy_name": "test_bot1",
            "is_running": True,
            "position_long": 0.001,
            "position_short": 0.001
        }
        pass
    else:
        google = google_utility(setting['google'])
        google_strategy = google.get_strategy(strategy_name)
        pass
    print(google_strategy)

    # 稼働か？
    is_running = google_strategy.get('is_running', False)
    if not is_running:
        print("注文Webhookが来ましたが、休止中のため取引を行いませんでした。")
        messages = line.get_messages_text(f'{strategy_name}: 注文Webhookが来ましたが、休止中のため取引を行いませんでした。')
        await line.broadcast_send(messages, True)
        return '200'

    async with pybotters.Client(apis=apis, base_url=base_url) as client:
        queue = []

        if trade_category == 'close_all':
            # 現在の保持ポジ数
            position_long: float = google_strategy.get('position_long', 0)
            position_short: float = google_strategy.get('position_short', 0)

            if position_long == 0 and position_short == 0:
                print('決済Webhookが来ましたが、保持ポジションがありませんでした。')
                messages = line.get_messages_text(f'{strategy_name}: 決済Webhookが来ましたが、保持ポジションがありませんでした。')
                await line.broadcast_send(messages, True)
                return '200'

            if position_long != 0:
                # ポジションがあれば逆決済
                data = {'symbol': symbol, 'side': env.BINANCE_SELL, 'type': 'MARKET', 'quantity': position_long}
                queue.append(data)
                pass

            if position_short != 0:
                # ポジションがあれば逆決済
                data = {'symbol': symbol, 'side': env.BINANCE_BUY, 'type': 'MARKET', 'quantity': position_short}
                queue.append(data)
                pass
            pass

        elif trade_category == 'close_long':
            position_long: float = google_strategy.get('position_long', 0)

            if position_long == 0:
                print('決済Webhookが来ましたが、保持ポジションがありませんでした。')
                messages = line.get_messages_text(f'{strategy_name}: 決済Webhookが来ましたが、保持ポジションがありませんでした。')
                await line.broadcast_send(messages, True)
                return '200'

            else:
                data = {'symbol': symbol, 'side': env.BINANCE_SELL, 'type': 'MARKET', 'quantity': position_long}
                queue.append(data)
                pass
            pass

        elif trade_category == 'close_short':
            position_short: float = google_strategy.get('position_short', 0)

            if position_short == 0:
                print('決済Webhookが来ましたが、保持ポジションがありませんでした。')
                messages = line.get_messages_text(f'{strategy_name}: 決済Webhookが来ましたが、保持ポジションがありませんでした。')
                await line.broadcast_send(messages, True)
                return '200'

            else:
                data = {'symbol': symbol, 'side': env.BINANCE_BUY, 'type': 'MARKET', 'quantity': position_short}
                queue.append(data)
                pass
            pass

        elif trade_category == 'buy':
            data = {'symbol': symbol, 'side': env.BINANCE_BUY, 'type': 'MARKET', 'quantity': quantity}
            queue.append(data)
            pass

        elif trade_category == 'sell':
            data = {'symbol': symbol, 'side': env.BINANCE_SELL, 'type': 'MARKET', 'quantity': quantity}
            queue.append(data)
            pass

        else:
            pass

        # 注文非同期実行
        results = await asyncio.gather(*[order_binance(client, q, symbol) for q in queue])

        queue = []
        for data in results:
            if data is None:
                continue

            if not google is None:
                google.add_history(strategy_name, [
                    data['orderId'],
                    data['symbol'],
                    data['side'],
                    data['type'],
                    data['avgPrice'],
                    data['executedQty'],
                    data['time']
                ])
                pass

            messages = line.get_order_messages(
                "約定のお知らせ", [
                    {'title': 'ストラテジー名', 'text': strategy_name},
                    {'title': '取引所', 'text': exchange},
                    {'title': '注文ID', 'text': data['orderId']},
                    {'title': '取引銘柄', 'text': data['symbol']},
                    {'title': '売買区分', 'text': convert_side(data['side'])},
                    {'title': '注文タイプ', 'text': convert_type(data['type'])},
                    {'title': '価格', 'text': convert_price(data['avgPrice'])},
                    {'title': '数量', 'text': convert_qty(data['executedQty'])},
                    {'title': '約定日時', 'text': convert_time_binance(data['time'])}])
            queue.append(messages)
            pass

        # LINE通知非同期実行
        await asyncio.gather(*[line.broadcast_send(q) for q in queue])

        if not google is None:
            # 保持ポジ数
            position_long: float = google_strategy.get('position_long', 0)
            position_short: float = google_strategy.get('position_short', 0)

            if trade_category == 'close_all':
                position_long = 0
                position_short = 0
                pass

            elif trade_category == 'close_long':
                position_long = 0
                pass

            elif trade_category == 'close_short':
                position_short = 0
                pass

            elif trade_category == 'buy':
                position_long = position_long + float(data['executedQty'])
                pass

            elif trade_category == 'sell':
                position_short = position_short + float(data['executedQty'])
                pass

            else:
                pass

            google.set_strategy(strategy_name, 'position_long', position_long)
            google.set_strategy(strategy_name, 'position_short', position_short)
            google.update_strateges_setting()
            print(f'position_long={position_long}, position_short={position_short}')

            messages_text = f"{strategy_name}: 現在の保持ポジションは下記の通りです。\nロング= {position_long} BTC\nショート= {position_short} BTC"
            messages = line.get_messages_text(messages_text)
            await line.broadcast_send(messages)
            pass

        pass
    return '200'


async def order_binance(client: pybotters.Client, data: dict, symbol: str):

    # 注文
    print('/fapi/v1/order')
    print(data)
    resp = await client.post('/fapi/v1/order', data=data)
    if resp.status != 200:
        print("注文に失敗しました。")
        return None

    data = await resp.json()
    print(data)
    if data is None:
        print("注文に失敗しました。")
        return None

    await asyncio.sleep(5)
    orderId = data['orderId']
    data = {'symbol': symbol, 'orderId': orderId}

    # 約定確認
    print('/fapi/v1/order')
    print(data)
    resp = await client.get('/fapi/v1/order', params=data)
    if resp.status != 200:
        print("注文に失敗しました。")
        return None

    data = await resp.json()
    print(data)
    if data is None:
        print("注文に失敗しました。")
        return None

    return data


async def bybit_order_main(strategy_name: str, trade_category: str, setting: dict):

    line = line_utility(setting['line'])

    # 売買区分が想定通りか
    if 'sell' != trade_category and 'buy' != trade_category and 'close_all' != trade_category and 'close_long' != trade_category and 'close_short' != trade_category:
        print('trade category does not match.')
        messages = line.get_messages_text(f'{strategy_name}: trade category does not match.')
        await line.broadcast_send(messages, True)
        return abort(500)

    # ストラテジー取得
    target_strategy = get_strategy(setting, strategy_name)
    quantity = target_strategy.get('quantity')
    exchange = target_strategy.get('exchange')
    symbol = target_strategy.get('symbol')

    # APIキー確認
    target_exchange = get_exchange(setting, exchange)
    if target_exchange is None or target_exchange.get('api_key', '') == '' or target_exchange.get('api_secret', '') == '':
        print("API key or secret key has not been set.")
        messages = line.get_messages_text(f'{strategy_name}: API key or secret key has not been set.')
        await line.broadcast_send(messages, True)
        return abort(500)

    apis = {}
    base_url = ''

    # testnet確認
    if 'testnet' in exchange:
        apis = {"bybit_testnet": [target_exchange.get('api_key', ''), target_exchange.get('api_secret', '')]}
        base_url = 'https://api-testnet.bybit.com'
        pass
    else:
        apis = {"bybit": [target_exchange.get('api_key', ''), target_exchange.get('api_secret', '')]}
        base_url = 'https://api.bybit.com'
        pass

    print(base_url)

    google = None
    if __name__ == '__main__':
        # デバッグ用
        google_strategy = {
            "strategy_name": "test_bot1",
            "is_running": True,
            "position_long": 0.001,
            "position_short": 0.001
        }
        pass
    else:
        google = google_utility(setting['google'])
        google_strategy = google.get_strategy(strategy_name)
        pass
    print(google_strategy)

    # 稼働か？
    is_running = google_strategy.get('is_running', False)
    if not is_running:
        print("注文Webhookが来ましたが、休止中のため取引を行いませんでした。")
        messages = line.get_messages_text(f'{strategy_name}: 注文Webhookが来ましたが、休止中のため取引を行いませんでした。')
        await line.broadcast_send(messages, True)
        return '200'

    async with pybotters.Client(apis=apis, base_url=base_url) as client:
        queue = []

        if trade_category == 'close_all':
            # 現在の保持ポジ数
            position_long: float = google_strategy.get('position_long', 0)
            position_short: float = google_strategy.get('position_short', 0)

            if position_long == 0 and position_short == 0:
                print('決済Webhookが来ましたが、保持ポジションがありませんでした。')
                messages = line.get_messages_text(f'{strategy_name}: 決済Webhookが来ましたが、保持ポジションがありませんでした。')
                await line.broadcast_send(messages, True)
                return '200'

            if position_long != 0:
                # ポジションがあれば逆決済
                data = {'symbol': symbol, 'side': env.BYBIT_SELL, 'order_type': 'Market', 'qty': position_long, 'time_in_force': 'GoodTillCancel', 'reduce_only': True, 'close_on_trigger': True}
                queue.append(data)
                pass

            if position_short != 0:
                # ポジションがあれば逆決済
                data = {'symbol': symbol, 'side': env.BYBIT_BUY, 'order_type': 'Market', 'qty': position_short, 'time_in_force': 'GoodTillCancel', 'reduce_only': True, 'close_on_trigger': True}
                queue.append(data)
                pass
            pass

        elif trade_category == 'close_long':
            position_long: float = google_strategy.get('position_long', 0)

            if position_long == 0:
                print('決済Webhookが来ましたが、保持ポジションがありませんでした。')
                messages = line.get_messages_text(f'{strategy_name}: 決済Webhookが来ましたが、保持ポジションがありませんでした。')
                await line.broadcast_send(messages, True)
                return '200'

            else:
                data = {'symbol': symbol, 'side': env.BYBIT_SELL, 'order_type': 'Market', 'qty': position_long, 'time_in_force': 'GoodTillCancel', 'reduce_only': True, 'close_on_trigger': True}
                queue.append(data)
                pass
            pass

        elif trade_category == 'close_short':
            position_short: float = google_strategy.get('position_short', 0)

            if position_short == 0:
                print('決済Webhookが来ましたが、保持ポジションがありませんでした。')
                messages = line.get_messages_text(f'{strategy_name}: 決済Webhookが来ましたが、保持ポジションがありませんでした。')
                await line.broadcast_send(messages, True)
                return '200'

            else:
                data = {'symbol': symbol, 'side': env.BYBIT_BUY, 'order_type': 'Market', 'qty': position_short, 'time_in_force': 'GoodTillCancel', 'reduce_only': True, 'close_on_trigger': True}
                queue.append(data)
                pass
            pass

        elif trade_category == 'buy':
            data = {'symbol': symbol, 'side': env.BYBIT_BUY, 'order_type': 'Market', 'qty': quantity, 'time_in_force': 'GoodTillCancel', 'reduce_only': False, 'close_on_trigger': False}
            queue.append(data)
            pass

        elif trade_category == 'sell':
            data = {'symbol': symbol, 'side': env.BYBIT_SELL, 'order_type': 'Market', 'qty': quantity, 'time_in_force': 'GoodTillCancel', 'reduce_only': False, 'close_on_trigger': False}
            queue.append(data)
            pass

        else:
            pass

        # 注文非同期実行
        results = await asyncio.gather(*[order_bybit(client, q, symbol) for q in queue])

        queue = []
        for data in results:
            if data is None:
                continue

            if not google is None:
                google.add_history(strategy_name, [
                    data['order_id'],
                    data['symbol'],
                    data['side'],
                    data['order_type'],
                    data['last_exec_price'],
                    data['qty'],
                    data['created_time']
                ])
                pass

            messages = line.get_order_messages(
                "約定のお知らせ", [
                    {'title': 'ストラテジー名', 'text': strategy_name},
                    {'title': '取引所', 'text': exchange},
                    {'title': '注文ID', 'text': data['order_id']},
                    {'title': '取引銘柄', 'text': data['symbol']},
                    {'title': '売買区分', 'text': convert_side(data['side'])},
                    {'title': '注文タイプ', 'text': convert_type(data['order_type'])},
                    {'title': '価格', 'text': convert_price(data['last_exec_price'])},
                    {'title': '数量', 'text': convert_qty(data['qty'])},
                    {'title': '約定日時', 'text': convert_time_bybit(data['created_time'])}])
            queue.append(messages)
            pass

        # LINE通知非同期実行
        await asyncio.gather(*[line.broadcast_send(q) for q in queue])

        if not google is None:
            # 保持ポジ数
            position_long: float = google_strategy.get('position_long', 0)
            position_short: float = google_strategy.get('position_short', 0)

            if trade_category == 'close_all':
                position_long = 0
                position_short = 0
                pass

            elif trade_category == 'close_long':
                position_long = 0
                pass

            elif trade_category == 'close_short':
                position_short = 0
                pass

            elif trade_category == 'buy':
                position_long = position_long + float(data['qty'])
                pass

            elif trade_category == 'sell':
                position_short = position_short + float(data['qty'])
                pass

            else:
                pass

            google.set_strategy(strategy_name, 'position_long', position_long)
            google.set_strategy(strategy_name, 'position_short', position_short)
            google.update_strateges_setting()
            print(f'position_long={position_long}, position_short={position_short}')

            messages_text = f"{strategy_name}: 現在の保持ポジションは下記の通りです。\nロング= {position_long} BTC\nショート= {position_short} BTC"
            messages = line.get_messages_text(messages_text)
            await line.broadcast_send(messages)
            pass

        pass
    return '200'


async def order_bybit(client: pybotters.Client, data: dict, symbol: str):

    # 注文
    print('/private/linear/order/create')
    print(data)
    resp = await client.post('/private/linear/order/create', data=data)
    if resp.status != 200:
        print("注文に失敗しました。")
        return None

    data = await resp.json()
    print(data)
    data = data['result']
    if data is None:
        print("注文に失敗しました。")
        return None

    await asyncio.sleep(5)
    orderId = data['order_id']
    data = {'symbol': symbol, 'order_id': orderId}

    # 約定確認
    print('/private/linear/order/search')
    print(data)
    resp = await client.get('/private/linear/order/search', params=data)
    if resp.status != 200:
        print("注文に失敗しました。")
        return None

    data = await resp.json()
    print(data)
    data = data['result']
    if data is None:
        print("注文に失敗しました。")
        return None

    return data


async def order_main(request):

    # 設定情報読み込み
    setting: dict = None
    with open('./setting.json', 'r') as f:
        setting = json.load(f)
        pass

    line = line_utility(setting['line'])

    try:

        # POSTメソッドのみ
        print(f'method={request.method}')
        if request.method != 'POST':
            print('POST Method Only.')
            messages = line.get_messages_text('POST Method Only.')
            await line.broadcast_send(messages)
            return abort(403)

        # text/plain のみ
        content_type: str = request.headers['content-type']
        print(f'content_type={content_type}')
        if not 'text/plain' in content_type.lower():
            print('Content Type is Plain Text Only.')
            messages = line.get_messages_text('Content Type is Plain Text Only.')
            await line.broadcast_send(messages)
            return abort(403)

        request_json = request.get_json(silent=True)
        print(f'request_json={request_json}')

        request_args = request.args
        print(f'request_args={request_args}')

        request_data: str = request.data.decode('utf-8', 'ignore')
        print(f"request_data={request_data}")

        request_split = request_data.split(' ')
        print(f'request_split.len={len(request_split)}')
        if len(request_split) != 2:
            # リクエスト不正
            print('Request is not correct.')
            messages = line.get_messages_text(f'Request is not correct.\nRequest="{request_data}"')
            await line.broadcast_send(messages)
            return abort(400)

        strategy_name = request_split[0]
        side = request_split[1]

        # ストラテジー確認
        target_strategy = get_strategy(setting, strategy_name)
        if target_strategy is None:
            print('Strategy name does not match.')
            messages = line.get_messages_text('Strategy name does not match.')
            await line.broadcast_send(messages)
            return abort(500)

        print(target_strategy)

        exchange = target_strategy.get('exchange', '')

        # 取引所
        if 'binance' in exchange:
            result = await binance_order_main(strategy_name, side, setting)
            return result

        elif 'bybit' in exchange:
            result = await bybit_order_main(strategy_name, side, setting)
            return result

        # 想定外の取引所
        print("Exchange is not correct. Please check.")
        messages = line.get_messages_text('Exchange is not correct. Please check.')
        await line.broadcast_send(messages)
        return abort(500)

    except Exception as e:
        messages = line.get_messages_text(f'システムエラーが発生しました。\n{str(e)}')
        await line.broadcast_send(messages)
        raise


def convert_status(status: str):
    return '新規' if status.lower() == 'new' else '決済'


def convert_side(side: str):
    return '売' if side.lower() == 'sell' else '買'


def convert_type(type: str):
    return '成行' if type.lower() == 'market' else '指値'


def convert_price(price: str):
    return round(float(price), 2)


def convert_qty(qty: str):
    return f'{qty} BTC'


def convert_time_binance(time: float):
    dt1 = dt.datetime.fromtimestamp(time * 0.001, tz=dt.timezone.utc)
    return (dt1+dt.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")


def convert_time2(dt_now: dt.datetime):
    dt1 = dt.datetime.fromtimestamp(dt_now.timestamp, tz=dt.timezone.utc)
    return (dt1+dt.timedelta(hours=9)).strftime("%Y%m%d%H%M%S")


def convert_time_bybit(str: str):
    # "2020-08-10T19:28:56Z"
    dt1 = dt.datetime.strptime(str, '%Y-%m-%dT%H:%M:%SZ')
    return (dt1+dt.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")


async def line_bot_main(request):

    if request.method == 'POST':
        request_json = request.get_json(silent=True)

        # 設定情報読み込み
        setting = None
        with open('./setting.json', 'r') as f:
            setting = json.load(f)
            pass

        line = line_utility(setting['line'])
        google = google_utility(setting['google'])

        if request_json and 'events' in request_json:
            events: list = request_json['events']
            for event in events:
                print(event)

                if event['type'] == 'message' and event['message']['text'].find(env.MENU1_OPERATING_STATUS_CONFIRMATION) == 0:
                    # 稼働状況の確認

                    strateges = []
                    for setting_strategy in setting.get('strateges'):
                        target_strategy = google.get_target_strategy(setting_strategy)
                        if target_strategy is None:
                            text = f"未設定"
                            pass
                        else:
                            running_text = '稼働' if target_strategy.get('is_running', False) else '休止'
                            text = f"{running_text}中"
                            pass

                        strateges.append({"text1": setting_strategy.get('strategy_name'), "text2": f"【{setting_strategy.get('exchange')}】{text}"})
                        pass

                    messages = line.get_operating_status(env.MENU1_OPERATING_STATUS_CONFIRMATION, strateges)
                    pass

                elif event['type'] == 'message' and event['message']['text'].find(env.MENU2_CHANGE_SETTING) == 0:
                    # 設定の変更

                    strateges = []
                    for setting_strategy in setting.get('strateges'):
                        strateges.append({"label": setting_strategy.get('strategy_name'), "text": f"{setting_strategy.get('strategy_name')}: {env.MENU2_CHANGE_SETTING}", "style": "primary"})
                        pass

                    messages = line.get_menu(env.MENU2_CHANGE_SETTING, strateges)
                    google.set1('last_messages', f"{env.MENU2_CHANGE_SETTING}-1")
                    pass

                elif event['type'] == 'message' and google.get_dict_value('last_messages', '').find(f"{env.MENU2_CHANGE_SETTING}-1") == 0:
                    # 設定の変更

                    target_strategy: dict = None
                    strateges = setting.get('strateges')
                    for i in range(len(strateges)):
                        if event['message']['text'].find(strateges[i].get('strategy_name')) == 0:
                            target_strategy = strateges[i]
                            break
                        pass

                    if target_strategy is None:
                        messages = line.get_messages_text(env.CANCEL)
                        google.pop_all()
                        pass
                    else:
                        menu = [
                            {"label": env.CHANGE_OPERATION, "text": f"{target_strategy.get('strategy_name')}: {env.CHANGE_OPERATION}", "style": "primary"},
                            {"label": env.POSITION_RESET, "text": f"{target_strategy.get('strategy_name')}: {env.POSITION_RESET}", "style": "secondary"}
                        ]
                        messages = line.get_menu(f"{target_strategy.get('strategy_name')}: {env.MENU2_CHANGE_SETTING}", menu)
                        google.set1('last_messages', f"{env.MENU2_CHANGE_SETTING}-2")
                        pass

                elif event['type'] == 'message' and google.get_dict_value('last_messages', '').find(f"{env.MENU2_CHANGE_SETTING}-2") == 0:
                    # 設定の変更

                    target_strategy: dict = None
                    strateges = setting.get('strateges')
                    for i in range(len(strateges)):
                        if event['message']['text'].find(strateges[i].get('strategy_name')) == 0:
                            target_strategy = strateges[i]
                            break
                        pass

                    if target_strategy is None:
                        messages = line.get_messages_text(env.CANCEL)
                        google.pop_all()
                        pass
                    else:

                        if event['message']['text'].find(env.CHANGE_OPERATION) != -1:
                            # 稼働状況の変更
                            messages = line.get_messages_ok_cancel(
                                f"{target_strategy.get('strategy_name')}: {env.CHANGE_OPERATION}",
                                "",
                                {"label": env.RUN, "text": f"{target_strategy.get('strategy_name')}: {env.RUN}"},
                                {"label": env.STOP, "text": f"{target_strategy.get('strategy_name')}: {env.STOP}"})
                            google.set1('last_messages', f"{env.CHANGE_OPERATION}-2")
                            pass

                        elif event['message']['text'].find(env.POSITION_RESET) != -1:
                            # 保持ポジションのリセット
                            messages = line.get_messages_ok_cancel(
                                f"{target_strategy.get('strategy_name')}: {env.POSITION_RESET}",
                                "手動で決済した場合、設定上の保持ポジションが残ってしまうためリセットする必要があります。",
                                {"label": env.RESET, "text": f"{target_strategy.get('strategy_name')}: {env.RESET}"},
                                {"label": env.CANCEL, "text": f"{target_strategy.get('strategy_name')}: {env.CANCEL}"})
                            google.set1('last_messages', f"{env.POSITION_RESET}-2")
                            pass

                        else:
                            messages = line.get_messages_text(env.CANCEL)
                            google.pop_all()
                            pass
                        pass

                elif event['type'] == 'message' and google.get_dict_value('last_messages', '').find(f"{env.CHANGE_OPERATION}-2") == 0:
                    # 稼働状況の変更

                    target_strategy: dict = None
                    strateges = setting.get('strateges')
                    for i in range(len(strateges)):
                        if event['message']['text'].find(strateges[i].get('strategy_name')) == 0:
                            target_strategy = strateges[i]
                            break
                        pass

                    if target_strategy is None:
                        messages = line.get_messages_text(env.CANCEL)
                        pass
                    else:

                        if event['message']['text'].find(env.RUN) != -1:
                            messages = line.get_messages_text(f"自動取引を{env.RUN}しました。")
                            google.set_strategy(target_strategy.get('strategy_name'), 'is_running', True)
                            pass
                        else:
                            messages = line.get_messages_text(f"自動取引を{env.STOP}しました。")
                            google.set_strategy(target_strategy.get('strategy_name'), 'is_running', False)
                            pass
                        pass

                    google.pop_all()
                    pass

                elif event['type'] == 'message' and google.get_dict_value('last_messages', '').find(f"{env.POSITION_RESET}-2") == 0:
                    # 保持ポジションのリセット

                    target_strategy: dict = None
                    strateges = setting.get('strateges')
                    for i in range(len(strateges)):
                        if event['message']['text'].find(strateges[i].get('strategy_name')) == 0:
                            target_strategy = strateges[i]
                            break
                        pass

                    if target_strategy is None:
                        messages = line.get_messages_text(env.CANCEL)
                        pass
                    else:

                        if event['message']['text'].find(env.RESET) != -1:
                            messages = line.get_messages_text("保持ポジションをリセットしました。")
                            google.set_strategy(target_strategy.get('strategy_name'), 'position_long', 0)
                            google.set_strategy(target_strategy.get('strategy_name'), 'position_short', 0)
                            pass
                        else:
                            messages = line.get_messages_text(env.CANCEL)
                            google.pop_all()
                            pass
                        pass

                    google.pop_all()
                    pass

                else:
                    messages = line.get_other([env.MENU1_OPERATING_STATUS_CONFIRMATION, env.MENU2_CHANGE_SETTING])
                    google.pop_all()
                    pass
                await line.broadcast_send(messages, True)
                pass

            google.update_strateges_setting()
            pass
        pass

    return '200'


async def history_main(request):
    print(f'method={request.method}')

    if request.method != 'GET':
        print('GET Method Only.')
        return abort(403)

    request_args = request.args
    print(f'request_args={request_args}')

    # 設定情報読み込み
    setting = None
    with open('./setting.json', 'r') as f:
        setting = json.load(f)
        pass

    google = google_utility(setting['google'])

    history_data = google.get_history_data('binance')
    html = html_utility.get_history(history_data)

    return html


@functions_framework.http
def line_bot(request):
    return asyncio.run(line_bot_main(request))


@functions_framework.http
def order(request):
    return asyncio.run(order_main(request))


@functions_framework.http
def history(request):
    return asyncio.run(history_main(request))


if __name__ == '__main__':

    # 設定情報読み込み
    setting = None
    with open('./setting.json', 'r') as f:
        setting = json.load(f)
        pass

    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        pass

    asyncio.run(binance_order_main('test_bot3', 'buy', setting))
    pass
