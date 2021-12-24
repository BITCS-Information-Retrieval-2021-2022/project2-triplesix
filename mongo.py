import pymongo
import json
import os


def write():
    dirs = os.listdir("D:\\Code/PycharmProjects/aminerCrawl/json")
    mongoClient = pymongo.MongoClient(host="localhost", port=27017)
    crawler = mongoClient.crawler
    i = 0
    try:
        for dir in dirs:
            filename = "json/" + dir
            print(filename)
            with open(filename) as f:
                list = json.load(f)
                # print(len(list))
                for item in list:
                    # 通过update_one实现非重复插入
                    crawler.scholar.update_one({"name": item["name"], "citation": item["citation"]}, {'$set': item},
                                               upsert=True)
                    i = i + 1
                    print(i)
    except Exception as e:
        print(e)
        print("error")

    mongoClient.close()


if __name__ == '__main__':
    write()
