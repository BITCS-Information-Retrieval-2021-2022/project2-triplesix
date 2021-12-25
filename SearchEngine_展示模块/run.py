from flask import Flask, request, render_template, abort
import json
import requests

app = Flask(__name__)  # 程序入口


@app.route('/search', methods=['GET'])  # 检索页面
def search():  # 检索
    return render_template('search.html')


app.config['JSON_AS_ASCII'] = False


@app.route('/result', methods=['GET'])  # 文献页面
def result():  # 文献
    query_term = request.args.get("query")
    if not query_term:
        abort(404)
    url = "http://10.1.10.12:5002/search"
    body = {"keyword": query_term}
    respond = requests.post(url=url, json=body).content.decode('utf-8')
    json_data = json.loads(respond)
    total = len(json_data)  # 总词条数
    print(total)
    item_list = []
    for i in range(0, total):
        domain = ''
        for t in json_data[i]['domain']:
            domain = domain + t + ', '
        domain = domain.rstrip(' ').rstrip(',')
        print(domain)
        item = {"name": json_data[i]['name'],
                "domain": domain,
                "citation": json_data[i]['citation'],
                "department": json_data[i]['department'],
                "paper_list": json_data[i]['paper_list'],
                'url': '/author?name=' + json_data[i]['name']
                       + '&department=' + json_data[i]['department']}
        item_list.append(item)

    page_num = request.args.get("page_num", 1, type=int)  # 当前页码
    page_len = 2  # 页面词条数

    maxi = 1 + int(total / page_len)  # 总页数

    if page_num >= maxi:
        begin = total % page_len + (page_num - 1) * page_len
        end = total
    else:
        begin = (page_num - 1) * page_len + 1
        end = begin + page_len - 1

    if page_num >= 6:
        range_pages = range(page_num - 5, page_num + 5 if page_num + 5 < maxi else maxi)
    else:
        range_pages = range(1, maxi + 1 if maxi < 10 else 10)

    return render_template('result.html',  # 页面
                           query=query_term,  # 关键词
                           total=total,  # 总词条数
                           page_num=page_num,  # 起始页
                           page_len=page_len,  # 每页词条数
                           maxpage=maxi,  # 总页数
                           range_pages=range_pages,
                           results=item_list[begin - 1:end])


@app.route('/advertisement', methods=['GET'])  # 广告页面
def advertisement():  # 广告
    return render_template('advertisement.html')


@app.route('/author', methods=['GET'])
def author():  # 作者
    name = request.args.get("name")
    department = request.args.get("department")
    if not (name and department):
        abort(404)
    query_term = '%s&%s' % (name, department)
    url = "http://10.1.10.12:5002/author"
    body = {"keyword": query_term}
    respond = requests.post(url=url, json=body).content.decode('utf-8')
    json_data = json.loads(respond)

    name = json_data[0]['name']
    domain = ''
    for t in json_data[0]['domain']:
        domain = domain + t + ', '
    domain = domain.rstrip(' ').rstrip(',')
    author_relation_img = json_data[0]['author_relation_img']
    department = json_data[0]['department']
    paper_list = json_data[0]['paper_list']

    return render_template('author.html',
                           name=name,
                           domain=domain,
                           author_relation_img=author_relation_img,
                           department=department,
                           paper_list=paper_list)


app.run(port=5000, debug=True)
