import requests
import json
import pymongo
import time

# 设置MongoDB账户和数据集
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["Sem_sch_authors"]
mycoll = mydb["Authors_data"]

# 设置User-Agent防反爬
headers ={
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0'
}
# 将与该作者有关的作者ID存储起来
def get_all_authorId(aid):
    url = "https://api.semanticscholar.org/graph/v1/author/"+str(aid)+"?fields=url,papers.abstract,papers.authors"
    response = requests.get(url=url,headers=headers)
    content = response.text
    content = json.loads(content)
    first_layer_authors_id = []
    for item1 in content['papers']:
        for item2 in item1['authors']:
            first_layer_authors_id.append(item2['authorId'])
    print("作者ID" + str(aid) + "相关作者ID收集完毕！")
    # 爬取第二层人物关系
    # second_layer_authors_id = []
    # for i in range(0,len(first_layer_authors_id)):
    #     url1 = "https://api.semanticscholar.org/graph/v1/author/" + str(first_layer_authors_id[i]) + "?fields=url,papers.abstract,papers.authors"
    #     response1 = requests.get(url=url1, headers=headers)
    #     content1 = response1.text
    #     content1 = json.loads(content1)
    #     for item1 in content1['papers']:
    #         for item2 in item1['authors']:
    #             second_layer_authors_id.append(item2['authorId'])
    #     print("作者ID"+str(first_layer_authors_id[i])+"相关作者ID收集完毕！")
    # # 将两层挖掘的ID存到一起
    all_layer_authors_id = first_layer_authors_id # + second_layer_authors_id
    return all_layer_authors_id

# 设置一个起始大牛作者
authors = get_all_authorId("48727916")

len_author = len(authors) # 作者列表id数量
len_list = 0 # 当前爬取的作者数量
for i in range(0, len_author-1):
    len_list += 1
    print("剩余", str(len_author - len_list), "个目标")
    dict = {}
    url = "https://api.semanticscholar.org/graph/v1/author/" + str(authors[i]) + "?fields=url,externalIds,name,aliases,affiliations,homepage,papers.abstract,papers.authors"
    response = requests.get(url=url, headers=headers)
    time.sleep(5)
    content = response.text
    content = json.loads(content)
    dict = content
    # 将数据存入MongoDB
    Insert_mongoDB = mycoll.insert_one(dict)
    print("作者ID" + str(authors[i]) + "信息已更新！")
