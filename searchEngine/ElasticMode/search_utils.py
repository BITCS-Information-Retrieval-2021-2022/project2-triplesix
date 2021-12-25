# -*- coding:utf-8 -*-
# @Author : tzy

from elasticsearch import Elasticsearch, helpers

import ElasticMode.logModule as log
from ElasticMode.data_utils import clean_data, post_process


class ElasticSearchEngine:

    def __init__(self, ip = 'localhost', port = 9200, timeout = 3600, index = 'scholar'):
        self.es = Elasticsearch(host = ip, port = port, timeout = timeout)
        self.index = index

        if not self.es.indices.exists(self.index):
            self.es.indices.create(self.index)
            msg = "The current index does not exist, a new index has been created: {}".format(self.index)
            log.INFO(msg)

    def insert(self, doc_type, body):
        msg = self.es.index(self.index, doc_type, body = body)
        log.INFO(msg)

    def update(self, id, body, condition = False):
        if condition:
            msg = self.es.update_by_query(self.index, id = id, body = body)
        else:
            msg = self.es.update(self.index, id = id, body = body)
        log.INFO(msg)

    def delete(self, id, body, condition = False):
        if condition:
            msg = self.es.delete_by_query(self.index, id = id, body = body)
        else:
            msg = self.es.delete(self.index, id = id, body = body)
        log.INFO(msg)

    #   批量插入
    def bulk_insert(self):
        data = clean_data()
        body = [{"_index": self.index, "_type": "_doc", "_source": value} for value in data]
        helpers.bulk(self.es, body)

    def _search(self, body, size):
        result = self.es.search(index = self.index, body = body, size = size)
        # result = result["hits"]["hits"]
        return result

    def search_by_keyword(self, keyword):
        body = {
            'query':{
                'bool':{
                    'should': [{"match_phrase":{"name":keyword}},
                             {"match":{"domain":keyword}},
                             {"match":{"department":keyword}},
                             {"match":{"paper_list":keyword}}]
                }
            },
            "collapse":{
                "field": "name.keyword"
            }
        }
        result = self._search(body = body, size = 20)
        result = post_process(result)
        return result

    def search_by_author(self, name, department):
        body = {
            'query':{
                'bool':{
                    'must': [{"match_phrase":{"name":name}},
                             {"match":{"department":department}}]
                }
            },
            "_source":{
                "includes": ["name", "domain", "department", "paper_list"]
            },
            "collapse":{
                "field": "name.keyword"
            }
        }
        result = self._search(body = body, size = 1)
        result = post_process(result, True)
        return result


if __name__ == "__main__":
    es = ElasticSearchEngine()
    es.bulk_insert()