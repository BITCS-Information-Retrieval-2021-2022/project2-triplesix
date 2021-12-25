# -*-coding:utf-8-*-
# author lyl
import json
import os
import hashlib
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import io
import base64
import matplotlib
from MatchMode.mongo_utils import MongoPipline
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['font.family'] = 'sans-serif'

matplotlib.use('Agg')

class DataProcess:
    def __init__(self, data):
        self.data = data

    def author_relation_compute(self, keyword: str=None):
        if not keyword:
            list(map(self._process_k, self.data))
        elif keyword == 'relation_authors':
            list(map(self._process_k_for_authors, self.data))
        elif keyword == 'relation_img':
            list(map(self.creat_relationship, self.data))
        else:
            raise ValueError('')
        return self.data
    
    def _process_k_for_authors(self, data, k=50):
        result = {}
        if not data['paper_list']:
            return []
        for paper in data['paper_list']:
            for name in paper[1]:
                result[name] = result.get(name, 0) + 1
        result = sorted(result.items(), key=lambda x: x[1], reverse=True)
        # result = [item[0] for item in result[:k]]
        result = result[:k]
        data['author_relation'] = result
        return result

    def _process_k(self, data, k=50):
        result = {}
        for paper in data['paper_list']:
            for name in paper[1]:
                result[name] = result.get(name, 0) + 1
        result = sorted(result.items(), key=lambda x: x[1], reverse=True)
        # result = [item[0] for item in result[:k]]
        result = result[:k]
        data['author_relation'] = result
        self.creat_relationship(data)
        return result

    def creat_relationship(self, data):
        relations = {(data['name'], item[0]): item[1] for item in data['author_relation']}
        fig = plt.figure(figsize=(12, 12))
        G = nx.Graph()
        for k, v in relations.items():
            G.add_nodes_from([k[0], k[1]])
        for k, v in relations.items():
            G.add_edge(k[0], k[1], weight=v, length=10.0)

        pos = nx.spring_layout(G)
        # 设置节点样式
        # 前k个节点
        nx.draw_networkx_nodes(G, pos, alpha=0.8, node_size=100)
        nx.draw_networkx_edges(G, pos, edgelist=relations.keys(), width=1, alpha=0.9, edge_color='g')
        nx.draw_networkx_labels(G, pos, font_size=10)

        plt.axis('off')
        # 将图片转换成二进制流
        canvas = fig.canvas
        buffer = io.BytesIO()
        canvas.print_png(buffer)
        img_data = buffer.getvalue()
        buffer.close()

        data['author_relation_img'] = self._imageToStr(img_data)

    def _imageToStr(self, image):
        image_byte = base64.b64encode(image)
        image_str = image_byte.decode('ascii')  # byte类型转换为str
        return image_str

    def _strToImage(self, image_str):
        image_str = image_str.encode('ascii')
        image_byte = base64.b64decode(image_str)
        return image_byte


class DataPreProcess:
    def __init__(self):
        pass

    def _process(self, data):
        title = data.get('title', '')
        authors = [author_info['name'] for author_info in data['authors']]
        return [title, authors]

    def process_web(self, json_path, mode='web1'):
        data = MongoPipline.json_load(json_path)
        result = []
        for item in data:
            if not item.get('name', None):
                continue
            tmp_data = {
                "name": item.get('name', ''),
                "citation": item.get('citation', -1),
                "department": item.get('department', ""),
                "domain": item.get('domain', []),
                "paper_list": item.get("paper_list", None)
            }
            if tmp_data['paper_list'] is None:
                if item.get('papers', None):
                    tmp_data['paper_list'] = list(map(self._process, item['papers']))
                else:
                    continue
            result.append(tmp_data)
        return result

    def run(self, path, mode='web1'):
        result = []
        if os.path.isfile(path):
            result.extend(self.process_web(path, mode))
        elif os.path.isdir(path):
            for file in os.listdir(path):
                result.extend(self.process_web(os.path.join(path, file), mode))
        else:
            raise ValueError(f'{path} is not a correct file path or a dir path')
        return result