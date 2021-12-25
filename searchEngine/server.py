# -*- coding:utf-8 -*-
# @Author : tzy

import json
import time
import ElasticMode.logModule as log

from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
# 解决跨域问题
CORS(app, supports_credentials = True)

from MatchMode.mongo_utils import MongoDB, MongoPipline
from MatchMode.search_utils import SearchEngine
from ElasticMode.search_utils import ElasticSearchEngine

MODE = 2


@app.route("/search", methods = ["GET", "POST"])
def search():
    start = time.perf_counter()

    raw = request.get_data()
    data = json.loads(raw)
    keyword = data["keyword"]
    log.INFO("Keyword: {}, Mode: {}".format(keyword, MODE))

    if MODE == 1: # 匹配搜索
        tmp_result = match_search_engine.find(keyword)
        result = json.dumps(eval(str(tmp_result)))    
    if MODE == 2: # ES搜索
        tmp_result = elastic_search_engine.search_by_keyword(keyword)
        result = json.dumps(tmp_result)

    end = time.perf_counter()
    log.INFO("Time-consuming for this search: {:.4f}s".format(end - start))
    # log.INFO("Result: {}".format(result))

    return result


@app.route("/author", methods = ["GET", "POST"])
def author():
    start = time.perf_counter()

    raw = request.get_data()
    data = json.loads(raw)
    name, department = data["keyword"].split('&')
    log.INFO("Name: {}, Domain: {}, Mode: {}".format(name, department, MODE))

    if MODE == 1: # 匹配搜索
        tmp_result = match_search_engine.find_by_name(name, department=department)
        result = json.dumps(eval(str(tmp_result)))
    if MODE == 2: # ES搜索
        tmp_result = elastic_search_engine.search_by_author(name, department)
        result = json.dumps(tmp_result)

    end = time.perf_counter()
    log.INFO("Time-consuming for this search: {:.4f}s".format(end - start))
    # log.INFO("Result: {}".format(result))

    return result


if __name__ == "__main__":
    log.INFO("Initialize the matchMode search engine")
    db = MongoDB('mydb')
    mongo_pipline = MongoPipline(db)
    allData = mongo_pipline.load_data_from_mongo(do_filter = True)
    match_search_engine = SearchEngine(allData)

    log.INFO("Initialize the elasticMode search engine")
    elastic_search_engine = ElasticSearchEngine()

    log.INFO("Start the server")
    app.run(host = '0.0.0.0', port = 5002, debug = False)