# -*-coding:utf-8-*-
# author lyl
import pymongo
import os
import json
import hashlib


DIR_PATH = os.path.dirname(os.path.abspath(__name__))
DB_MAP = {'web1': 'web1_data', 'web2': 'web2_data'}


class MongoDB:

    def __init__(self, database, collection = None, ip = 'localhost', port = 27017):
        # 建立连接
        self.client = pymongo.MongoClient(ip, port)
        # 指定数据库
        self.db = self.client[database]
        # 指定集合
        if collection:
            self.collection = self.db[collection]
        else:
            self.collection = None

    def change_collection(self, collection):
        self.collection = self.db[collection]

    def insert(self, *data):
        if len(data) == 0:
            return
        if isinstance(data[0], list):
            assert len(data) == 1
            data = data[0]
        self.collection.insert_many(data)

    def find(self, data=dict({}), single=False):
        # 返回列表
        if single:
            cur = [self.collection.find_one(data)]
        else:
            cur = self.collection.find(data, {"_id": 0})
            cur = list(cur)
        return cur

    def update(self, data, new_data, single=False):
        if single:
            self.collection.update_one(data, {'$set': new_data})
        else:
            self.collection.update_many(data, {'$set': new_data})

    def delete(self, data, single=False):
        if single:
            self.collection.delete_one(data)
        else:
            self.collection.delete_many(data)


class MongoPipline:
    def __init__(self, db):
        self.dir_path = DIR_PATH
        self.db_map = DB_MAP
        self.db = db

    @classmethod
    def json_load(cls, path):
        with open(path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def writer_json_to_mongo(self, keyword=None, do_filter=False):
        if keyword is None:
            keyword = self.db_map.keys()
        elif isinstance(keyword, str):
            keyword = [keyword]
        for key in keyword:
            self.db.change_collection(self.db_map[key])
            data_path = os.path.join(self.dir_path, 'data', key, 'json')
            json_files = os.listdir(data_path)
            for json_file in json_files:
                data = self.json_load(os.path.join(data_path, json_file))[key]
                if do_filter:
                    self.db.insert(self.filter(data))
                else:
                    self.db.insert(data)

    def load_data_from_mongo(self, keyword=None, do_filter=False):
        if keyword is None:
            keyword = self.db_map.keys()
        elif isinstance(keyword, str):
            keyword = [keyword]
        result = []
        for key in keyword:
            self.db.change_collection(self.db_map[key])
            result.extend(self.db.find())
        result = result if not do_filter else self.filter(result)
        return result

    def clear_mongo_data(self, keyword=None):
        # assert self.db.collection, "MongoDB database collection must be specified"
        if keyword is None:
            keyword = self.db_map.keys()
        elif isinstance(keyword, str):
            keyword = [keyword]
        for key in keyword:
            self.db.change_collection(self.db_map[key])
            self.db.delete({})

    def writer_data_to_mongo(self, data: list, collection: str, do_filter=False):
        self.db.change_collection(collection)
        data = self.filter(data) if do_filter else data
        self.db.insert(data)

    def filter(self, data):
        result = []
        visited_dict = {}
        for item in data:
            info_id = item['name'].lower() + str(item['citation']) + item['department'].lower()
            m = hashlib.md5()
            m.update(info_id.encode('utf-8'))
            if not visited_dict.get(m.hexdigest(), None):
                result.append(item)
                visited_dict[m.hexdigest()] = 1
        return result