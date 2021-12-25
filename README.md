# project2-triplesix

## 1.爬虫模块

### 1.1 Aminer
#### 1.1.1 爬取策略
针对Aminer网站，采取基于关键词搜索的爬虫策略。例如，设置检索关键词为“Machine Learning”，网站会返回与关键词相关的一系列作者，我们爬取这些作者的姓名、照片链接、引用数、所属机构和领域信息，同时到每个作者的个人详情页面爬取该作者的所有论文列表，包括论文的题目和共同作者。通过设置不同的关键字，爬取不同的检索返回作者，最后将所有爬取到的数据进行去重操作。
#### 1.1.2 去重操作
在把包装好的数据写入MongoDB时，采用update_one方法，设置upsert=True，以达到不写入重复数据的目的。用法如下：

`collection.update_one(filter,new_values,upsert=True)`

`filter：查询的条件；`
`new_values：适用的修改；`
`upsert：update+insert，存在则更新，不存在则插入。`

### 1.2 Semantic Scholar
#### 1.2.1 爬取策略
由于网站提供了API的URL接口，其组成为 固定字符串 + authorID + 关键词 的形式，所以我们可以选择类似于树的层次遍历的方法，将作者ID充分利用起来。由一个大牛人物出发，首先遍历得到该人物的共同作者ID，再由得到的共同作者ID继续得到其相关作者的ID，最终就可以收集到一个庞大的关系树（实际上是关系网，但是后续有去重步骤）。最后将作者ID和固定字段组合形成作者信息的URL，访问该URL，拿到作者相关信息。
#### 1.2.2 去重及增量化
##### 1）去重
由于层次遍历阶段收集的是相关作者ID，并得到作者ID的列表，所以我们可以使用set的方法，直接对列表去重

`result = set(all_layer_authors_id) # 将list转为set直接去重`

`id_list = list(result) # 将set转回list方便使用`
##### 2）增量化
实现增量爬取的途径一般有以下几种：

**1. 使用数据库建立关键字段建立索引进行去重**。

**2. 根据URL地址进行去重**。适用于URL地址对应的数据不会变的情况，URL地址能够唯一判别一个条数据的情况，URL存在Redis中拿到URL地址，判断URL在Redis的URL的集合中是否存在。若存在，说明URL已经被请求过，不再请求；如果不存在，证明URL地址没有被请求过，那就发送请求，把该URL存入Redis的集合中。

**3. 布隆过滤器**。使用多个加密算法加密URL地址，得到多个值往对应值的位置把结果设置为1，新来一个URL地址，一样通过加密算法生成多个值，如果对应位置的值全为1，说明这个URL地址已经被抓过，如果没有被抓过，就把对应位置的值设置为1。

   可以发现增量爬取实现的利器便是Redis，Redis是一个开源的并且支持多种数据类型的存储系统，在很多项目当中都被用来当作数据持久化存储的选择。在程序中建立Redis数据库链接，通过Python的Redis库中的sadd函数进行URL的存储，使用sadd函数进行插入时，插入的数据也是键值对的形式，并且sadd函数继承了Redis利用键值自动去重的优势，如果插入的数据已经存在在数据库当中，则会返回0，如果是新数据，则将返回1。所以我们利用sadd函数向Redis中插入URL，如果返回值为1，则进行数据爬取，将对应的URL的数据爬取下来，以此来实现数据的增量爬取。实现数据爬取的自动化，则需要结合服务器，每天定时爬取。

### 1.3 MongoDB数据库

MongoDB是一个基于分布式文件存储的数据库。由C++语言编写。旨在为WEB应用提供可扩展的高性能数据存储解决方案。MongoDB是一个介于关系数据库和非关系数据库之间的产品，是非关系数据库当中功能最丰富，最像关系数据库的。它支持的数据结构非常松散，是类似json的bson格式，因此可以存储比较复杂的数据类型。Mongo最大的特点是它支持的查询语言非常强大，其语法有点类似于面向对象的查询语言，几乎可以实现类似关系数据库单表查询的绝大部分功能，而且还支持对数据建立索引。
```
# 设置MongoDB账户和数据集
myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["Sem_sch_authors"]

mycoll = mydb["Authors_data"]
```
```
# 将数据存入MongoDB

Insert_mongoDB = mycoll.insert_one(dict)

print("作者ID" + str(authors[i]) + "信息已更新！")
```

## 2.检索模块

### 2.1 MatchSearch
#### 1）将数据清洗格式化处理存入MongoDB数据库中
    db = MongoDB('mydb')
    mongo_pipline = MongoPipline(db)
    mongo_pipline.clear_mongo_data()
    # 数据预处理，包括数据清洗去重及格式化
    data_pre_process = DataPreProcess()
    web1_data = data_pre_process.run(r'./data/scholar.json')
    web2_data = data_pre_process.run(r'./data/Authors_data_Big.json')
    # 计算前50个共同作者
    data_process1 = DataProcess(web1_data)
    web1_data = data_process1.author_relation_compute('relation_authors')
    data_process2 = DataProcess(web2_data)
    web2_data = data_process2.author_relation_compute('relation_authors')
    # 存入MongoDB中
    mongo_pipline.writer_data_to_mongo(web1_data, 'web1_data', do_filter=True)
    mongo_pipline.writer_data_to_mongo(web2_data, 'web2_data', do_filter=True)
#### 2）实现SearchEngine类用于匹配检索，从MongoDB中读取数据实现综合检索，输入作者姓名、作者机构、领域、论文名称，都能得到相应的检索结果，并对结果去重


### 2.2 ElasticSearch

#### 2.2.1 ElasticSearch简介

Elasticsearch 是一个实时的分布式存储、搜索、分析的引擎。
##### 1）内置分词器，存储与检索阶段均支持分词处理
##### 2）采用倒排索引，支持模糊搜索
##### 3）采用 TF-IDF 计算文档相似性，并按评分排序将检索结果返回

#### 2.2.2 实现
##### 1）将数据清洗后批量插入到elasticsearch中
```
def bulk_insert(self):
   data = clean_data()
   body = [{"_index": self.index, "_type": "_doc", "_source": value} for value in data]
   helpers.bulk(self.es, body)
```
##### 2）实现 ElasticSearchEngine类，支持多字段（姓名、机构、领域、论文名称等）的模糊匹配，并对结果去重处理
```
from elasticsearch import Elasticsearch, helpers

class ElasticSearchEngine:

    def __init__(self, ip = 'localhost', port = 9200, timeout = 3600, index = 'scholar'):
        self.es = Elasticsearch(host = ip, port = port, timeout = timeout)
        self.index = index

        if not self.es.indices.exists(self.index):
            self.es.indices.create(self.index)
            msg = "The current index does not exist, a new index has been created: {}".format(self.index)
            log.INFO(msg)
...
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
result = self.es.search(index = self.index, body = body, size = size)
```
### 2.3 计算作者关系，绘图，将二进制转为字符串，构造 response json
#### 1) 根据爬取的数据，计算作者论文所有共同作者中出现频率最高的前50个共同作者
    def _process_k(self, data, k=50):
        result = {}
        for paper in data['paper_list']:
            for name in paper[1]:
                result[name] = result.get(name, 0) + 1
        result = sorted(result.items(), key=lambda x: x[1], reverse=True)
        result = result[:k]
        data['author_relation'] = result
        self.creat_relationship(data)
        return result
#### 2) 根据前50个共同作者绘制作者关系图
![image](https://user-images.githubusercontent.com/85541451/147380913-cc91d805-81e5-4c80-bebf-314e8d4dc408.png)

#### 3) 图片二进制转字符串
    def _imageToStr(self, image):
        image_byte = base64.b64encode(image)
        image_str = image_byte.decode('ascii')  # byte类型转换为str
        return image_str

### 2.4 Server
##### 1）采用 Flask 框架
##### 2）日志模块
##### 3）可选检索模式（匹配检索/ElasticSearch）
##### 4）处理请求 + 返回结果


## 3.展示模块
