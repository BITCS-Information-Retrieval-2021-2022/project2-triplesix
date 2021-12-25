# -*-coding:utf-8-*-
# author lyl
import hashlib
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Lock
import copy
from MatchMode.data_utils import DataProcess


class SearchEngine:
    def __init__(self, data: list):
        self.data = data

    @property
    def size(self):
        return len(self.data)

    def find(self, keyword: str=None):
        if not keyword:
            return self._filter(self.data)

        keyword = keyword.lower() 
        result = []
        for item in self.data:
            if keyword in item['name'].lower() or keyword in ' '.join([paper_info[0] for paper_info in item['paper_list']]).lower() or \
                keyword in item['department'].lower() or keyword in map(lambda x: x.lower(), item['domain']):
                result.append(item)
        return self.filter_by_key(copy.deepcopy(self._filter(result)), ["author_relation"])

    def find_by_name(self, name: str, department=None):
        if not department:
            result = [item for item in self.data if name.lower() in item['name'].lower()]
        else:
            result = [item for item in self.data if name.lower() in item['name'].lower() and department.lower() in item['department'].lower()] 
        
        tmp_result = self._filter(result)
        data_process = DataProcess(copy.deepcopy(tmp_result))
        tmp_result = data_process.author_relation_compute('relation_img')
        tmp_result = self.filter_by_key(tmp_result, ["author_relation", "citation"])
        return tmp_result

    def find_by_department(self, dep: str):
        result = [item for item in self.data if dep.lower() in item['department'].lower()]
        return self._filter(result)

    def find_by_domain(self, domain: str):
        result = [item for item in self.data if domain.lower() in map(lambda x: x.lower(), item['domain'])]
        return self._filter(result)

    def find_by_paper_name(self, paper_name: str):
        result = [item for item in self.data if paper_name.lower() in
                  ' '.join([paper_info[0] for paper_info in item['paper_list']]).lower()]
        return self._filter(result)

    def get_all(self):
        return self.data

    def _filter(self, data):
        # 根据作者姓名、引用数量、所属机构去重
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
    
    def filter_by_key(self, data, key_ls: list):
        result = []
        for item in data:
            for key in key_ls:
                if key in item.keys():
                    del item[key]
            result.append(item)
        return result
