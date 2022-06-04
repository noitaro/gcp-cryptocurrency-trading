from typing import Dict
from google.cloud import storage # pip install google-cloud-storage
import datetime as dt
import json

import environment as env

class google_utility:

    bucket = None
    strateges: dict = {}

    def __init__(self, setting) -> None:
        
        # Instantiates a client
        gcs = storage.Client()
        # Retrieve an existing bucket
        # https://console.cloud.google.com/storage/browser/[bucket-id]/
        self.bucket = gcs.get_bucket(setting['storage_bucket'])

        self.strateges: dict = {}
        blob = self.bucket.get_blob('strateges_setting.json')

        if not blob is None:
            # 存在する
            data = blob.download_as_text()
            self.strateges = json.loads(data)
            pass
        pass

    def update_strateges_setting(self):
        data = json.dumps(self.strateges)
        blob = self.bucket.blob('strateges_setting.json')
        blob.upload_from_string(data, content_type='application/json')
        pass



    def get_dict_value(self, key: str, default_value = None):
        value = self.strateges.get(key)

        if value is None:
            return default_value
        else:
            return self.strateges[key]

    def get2(self, key1: str, key2: str, default_value = None):
        exchange: dict = self.get_dict_value(key1, {})

        value = exchange.get(key2)
        if value is None:
            return default_value
        else:
            return exchange[key2]
        
    def set1(self, key: str, set_value):
        self.strateges[key] = set_value
        pass
        
    def set2(self, key1: str, key2: str, set_value):
        value = self.strateges.get(key1)

        if value is None:
            self.strateges[key1] = {}
            pass   
        
        self.strateges[key1][key2] = set_value
        pass
        

    def clear(self):
        self.strateges = {}
        pass

    def pop(self, key: str):
        value = self.strateges.get(key)

        if not value is None:
            self.strateges.pop(key, None)
            pass   
        
        pass

    def pop_all(self):
        self.pop('last_messages')
        self.pop('input_strategy')
        self.pop('input_api')
        self.pop('input_secret')
        self.pop('input_testnet')
        pass

    def add_history(self, strategy_name: str, history_data: list):
        history: str = 'OrderId,Symbol,Side,Type,Price,Qty,DateTime\n'
        history_name = f'history_{strategy_name}.csv'

        history_blob = self.bucket.get_blob(history_name)
        if history_blob is None:
            # 存在しない
            history_blob = self.bucket.blob(history_name)
            pass
        else:
            # 存在する
            history = history_blob.download_as_text()
            pass

        history = f"{history}{','.join(map(str, history_data))}\n"
        history_blob.upload_from_string(history.encode('utf-8'), content_type='text/csv')
        pass
    
    def get_history_name(self, key: str):
        strategy_name = self.get2(key, 'strategy_name', '')
        print(f'strategy_name: {strategy_name}')
        now = dt.datetime.now(tz=dt.timezone(dt.timedelta(hours=9)))
        history_name = f'history_{strategy_name}_{now.year}.csv'
        print(f'history_name: {history_name}')
        return history_name

    def get_history_data(self, strategy_name: str):
        history_name = f'history_{strategy_name}.csv'
        history_blob = self.bucket.get_blob(history_name)
        history_data = ''
        print(f'history_blob: {history_blob is None}')
        if not history_blob is None:
            # 存在する
            history_data = history_blob.download_as_text()
            pass
        return history_data

    def get_target_strategy(self, setting_strategy: dict):
        strateges: list = self.get_dict_value('strateges', [])

        for d in strateges:
            if d.get('strategy_name') == setting_strategy['strategy_name']:
                target_strategy: dict = d
                return target_strategy
            pass

        return None

    def get_strategy(self, strategy_name: str):

        if self.strateges.get('strateges') is None:
            self.strateges['strateges'] = []
            pass
        
        for i in range(len(self.strateges['strateges'])):
            if self.strateges['strateges'][i]['strategy_name'] == strategy_name:
                strategy: dict = self.strateges['strateges'][i]
                return strategy
            pass
        
        return {}

    def set_strategy(self, strategy_name: str, key: str, set_value):

        # 初期化
        if self.strateges.get('strateges') is None:
            self.strateges['strateges'] = []
            pass
        
        is_set = False
        for i in range(len(self.strateges['strateges'])):
            if self.strateges['strateges'][i]['strategy_name'] == strategy_name:
                is_set = True
                break
            pass
        
        if is_set == False:
            # 初期化
            self.strateges['strateges'].append({
                'strategy_name': strategy_name,
                'is_running': False,
                'position': 0
                })
            pass

        for i in range(len(self.strateges['strateges'])):
            if self.strateges['strateges'][i]['strategy_name'] == strategy_name:
                self.strateges['strateges'][i][key] = set_value
                return
            pass
        
        pass

    pass
