# -*- coding:utf-8 -*-
# @Author : tzy

import io
import os
import json
import base64
import matplotlib
import networkx as nx
import matplotlib.pyplot as plt

matplotlib.use('Agg')

import ElasticMode.logModule as log

MLPath = "../data/machine learning/json/"
NLPPath = "../data/Natural Language Processing/json/"
JsonDataPath = "../data/"
JsonData = ["AMiner.json", "SemanticScholar.json"]


def build_json_data():
    data = []

    for _, _, filenames in os.walk(MLPath):
        for filename in filenames:
            if os.path.splitext(filename)[1] == ".json":
                file = open(MLPath + filename, 'r')
                filedata = json.load(file)

                for item in filedata["machine learning"]:
                    data.append(item)
    
    for _, _, filenames in os.walk(NLPPath):
        for filename in filenames:
            if os.path.splitext(filename)[1] == ".json":
                file = open(NLPPath + filename, 'r')
                filedata = json.load(file)

                for item in filedata["Natural Language Processing"]:
                    data.append(item)
                
    with open("../data/AMiner.json", 'w') as f:
        f.write(json.dumps(data, ensure_ascii = False, indent = 4))


def _clean_paper_list(papers):
    paper_list = []
    for paper in papers:
        paper_item = []
        paper_item.append(paper["title"])
        common_author = []
        for author in paper["authors"]:
            common_author.append(author["name"])
        paper_item.append(common_author)
        paper_list.append(paper_item)
    return paper_list


def clean_data():
    data = []
    for jsondata in JsonData:
        file = open(JsonDataPath + jsondata, 'r')
        filedata = json.load(file)
        file.close()

        for item in filedata:
            if item.get("name", "") == "":
                continue
            else:
                name = item["name"]
            citation = item.get("citation", -1)
            department = item.get("department", "")
            domain = item.get("domain", [])
            if item.get("paper_list") == None:
                paper_list = _clean_paper_list(item["papers"])
            else:
                paper_list = item.get("paper_list", [])
            data.append({"name": name, 
                         "citation": citation, 
                         "department": department, 
                         "domain": domain, 
                         "paper_list": paper_list})

    return data


def _draw_relation_graph(name, items):
    relations = {(name, item[0]): item[1] for item in items}
    fig = plt.figure(figsize = (12, 12))
    G = nx.Graph()
    for k, v in relations.items():
        G.add_nodes_from([k[0], k[1]])
    for k, v in relations.items():
        G.add_edge(k[0], k[1], weight = v, length = 10.0)

    pos = nx.spring_layout(G)
    # 设置节点样式
    # 前k个节点
    nx.draw_networkx_nodes(G, pos, alpha = 0.8, node_size = 100)
    nx.draw_networkx_edges(G, pos, edgelist = relations.keys(), width = 1, alpha = 0.9, edge_color = 'g')
    nx.draw_networkx_labels(G, pos, font_size = 10)

    plt.axis('off')
    # 将图片转换成二进制流
    canvas = fig.canvas
    buffer = io.BytesIO()
    canvas.print_png(buffer)
    img_data = buffer.getvalue()
    buffer.close()
    return img_data


def _author_relation_compute(name, paper_list, k = 50):
    relation = {}
    for paper in paper_list:
        for author in paper[1]:
            if author == name:
                continue
            relation[author] = relation.get(author, 0) + 1
    
    items = list(relation.items())
    items.sort(key = lambda x : x[1], reverse = True)
    length = k if len(items) >= k else len(items)
    log.INFO("Author: {}, Relation num: {}, Relation: {}".format(name, length, items[:length]))

    return _draw_relation_graph(name, items[:length])


def _imageToStr(image):
    image_byte = base64.b64encode(image)
    image_str = image_byte.decode('ascii')  # byte类型转换为str
    return image_str


def _strToImage(str, filename):
    image_str = str.encode('ascii')
    image_byte = base64.b64decode(image_str)
    image_file = open(filename, 'wb')
    image_file.write(image_byte)
    image_file.close()


def post_process(data, relation = False):
    result = []
    for item in data['hits']['hits']:
        data = item["_source"]
        data["domain"] = data["domain"][:5] if len(data["domain"]) > 5 else data["domain"]
        if relation:
            data["author_relation_img"] = _imageToStr(
                                            _author_relation_compute(data['name'], data["paper_list"]))
        result.append(data)  
    return result


if __name__ == "__main__":
    # build_json_data()
    clean_data()