# -*- coding:utf-8 -*-
from selenium import webdriver
from lxml import etree
from single_item import Author
import json
import time
import requests
import os


class AminerSpider(object):
    def __init__(self, theme, driver):
        self.driver = driver
        self.theme = theme
        self.items = []
        self.sleeptime = 1
        self.second_parse_sleep = 1
        self.temp_sleep_time = [1.5, 2, 2.5, 3]
        self.username = u'***'  # 输入自己的Aminer用户名
        self.password = u'***'  # 输入自己的密码
        self.img_srcs = []
        self.author_infos = []
        self.file_count = 16  # 记录文件切片编号
        self.page = 8  # 开始的页面编号（从0开始)
        self.previous_page_author = ""

    def loginAminer(self, driver):
        # 登录操作
        time.sleep(self.second_parse_sleep)
        # driver.find_element_by_id('tabNav1').click()
        # driver.find_element_by_name('username').clear()
        # driver.find_element_by_name('username').send_keys(self.username)
        # driver.find_element_by_name('username').clear()
        driver.find_element_by_name('email').send_keys(self.username)
        driver.find_element_by_id('email').clear()
        driver.find_element_by_id('password').send_keys(self.password)
        driver.find_element_by_id('persist').click()
        # checkbox = driver.find_element_by_xpath('//div[@id="agreement"]')
        # html = etree.HTML(checkbox.get_attribute('innerHTML'))
        # print("html")
        # print(etree.tostring(html))
        # driver.execute_script("arguments[0].click();", checkbox)
        # checkbox.click()
        submit = driver.find_element_by_tag_name('button')
        submit.click()  # 登录提交
        time.sleep(self.sleeptime)

    def parse(self):
        # 解析网页，进行爬虫

        driver = self.driver
        loginUrl = 'https://www.aminer.cn/login'

        driver.get(loginUrl)
        self.loginAminer(driver)

        # 直接在跳转之后的网页上爬
        # 关键词搜索
        driver.find_element_by_tag_name('input').clear()
        driver.find_element_by_tag_name('input').send_keys(self.theme)
        submit = driver.find_element_by_css_selector("[class='ant-btn searchBtn ant-btn-lg']")
        submit.click()
        time.sleep(self.sleeptime)

        # 获取搜索返回数据的总页数，以及下一页的按钮位置
        total_page = int(driver.find_element_by_css_selector("[class='ant-pagination-simple-pager']")
                         .get_attribute('innerText')[1:])

        next_page_link = driver.find_element_by_xpath(
            '//*[@id="search_body"]/div[2]/div[3]/div[1]/div[2]/div[1]/div[3]/div[2]/div[2]/ul/li[3]')

        # 循环点击下一页按钮，到达要爬的页面
        for i in range(0, self.page):
            # next_page_link.click()
            driver.execute_script("arguments[0].click();", next_page_link)
            time.sleep(2)

        # 开爬
        for i in range(1, total_page - self.page + 1):
            div = driver.find_element_by_css_selector("[class="
                                                      "'a-aminer-components-expert-person-list-personList"
                                                      " person-list v1']")
            list_html = etree.HTML(div.get_attribute('innerHTML'))
            # 获取作者列表
            person_list = list_html.xpath("/html/body/div[@class='a-aminer-components-expert-c-person-item-personItem"
                                          " person-list-item']")
            prefix = 'https://www.aminer.cn'

            for person in person_list:
                # 针对每个作者爬取其图片、姓名、引用数、所属机构、领域
                detail_div = person.xpath('div')[0]
                img_src = detail_div.xpath("div[@class='imgBox']/a/img/@src")[0]
                # 解决没有对应图片的作者问题
                if not img_src.startswith('https:'):
                    img_src = 'https:' + img_src

                # 姓名
                name = \
                    detail_div.xpath("div[@class='content']/div[1]/div/div/a/strong/span/span[@class='name']/text()")[0]
                if name != self.previous_page_author:
                    # 判断该姓名是否与上一页的第一个作者相同，如果相同，说明之前的点击下一页操作失败了，就再点击下一页按钮
                    # 作者详情链接
                    profile_link = detail_div.xpath("div[@class='content']/div[1]/div/div/a/@href")[0]
                    # 引用数
                    citation = int(
                        detail_div.xpath('div[@class="content"]/div[2]/div/span[3]/span[@class="statst"]/text()')[0])
                    # 论文数，由于数据与实际不符，未录入数据库
                    paper_num = int(
                        detail_div.xpath('div[@class="content"]/div[2]/div/span[2]/span[@class="statst"]/text()')[0])
                    # 所属机构
                    department = detail_div.xpath('div[@class="content"]/div[3]/p[@class="person_info_item"]/text()')
                    # 有的前面有图标，有的没有；有的作者无机构信息
                    if len(department) == 2:
                        department = department[1]
                    elif len(department) == 1:
                        department = department[0]
                    else:
                        department = ""
                    # 领域，得到一个列表
                    domain = detail_div.xpath('div[@class="content"]/div[4]/div/span')
                    domain = domain[1:]
                    final_domain = []
                    for item in domain:
                        final_domain.append(item.xpath('a/text()')[0])

                    # 点进作者详情页爬取论文信息
                    second_driver = get_headless_webdriver()
                    interval = 3
                    paper_list = self.parse_paper_list_loop(prefix + profile_link, second_driver,
                                                            self.temp_sleep_time[interval])  # 爬取该作者的paperlist
                    second_driver.close()

                    # 数据包装
                    author = Author(name=name, img=img_src, citation=citation, paper_list=paper_list, theme=self.theme,
                                    department=department, domain=final_domain)
                    self.author_infos.append(author.print_to_json())
                    print(author.get_name())
                    self.img_srcs.append({'name': name, 'img_src': img_src[:-4]})

                    # 够10条就写入,下载作者图片
                    if len(self.author_infos) == 10:  # 每10个作者写成一个json
                        self.previous_page_author = self.author_infos[0]['name']
                        print(self.previous_page_author)
                        dump_to_json_file(author_infos=self.author_infos, theme=self.theme, file_count=self.file_count)
                        self.author_infos.clear()
                        download_imgs(self.img_srcs, self.theme, self.file_count)
                        self.img_srcs.clear()
                        self.file_count += 1

            # 点击下一页，进行爬取
            next_page_link.click()
            print('next_page_click')
            time.sleep(self.sleeptime * 5)
        # 最后不足10个的再写到json和下载图片
        if len(self.img_srcs) > 0:
            download_imgs(self.img_srcs, self.theme, self.file_count)
        if len(self.author_infos) > 0:
            dump_to_json_file(self.author_infos, self.theme, self.file_count)
        driver.close()

    def parse_paper_list(self, profile_url, driver, interval, count):
        # 爬取作者论文列表
        paper_name_list = []
        prefix = 'https://www.aminer.cn'
        try:
            # 尝试跳转到作者详情页面
            driver.get(profile_url)
        except Exception:
            time.sleep(self.sleeptime)
            try:
                # 再次尝试跳转
                paper_name_list(self, profile_url, driver, interval, count)
            except Exception:
                # 跳转失败，返回空列表
                return paper_name_list

        # 进行登录才能查看作者所有论文
        try:
            login_link_html_str = driver.find_element_by_css_selector('[class="info"]').get_attribute('innerHTML')
            login_link_html = etree.HTML(login_link_html_str)
        except Exception:
            # 此处是解决：在爬虫过程中，发现有的作者详情链接是空页面
            return paper_name_list
        if count == 0:
            login_link = prefix + login_link_html.xpath('//a/@href')[0]
            driver.get(login_link)
            # time.sleep(1)
            self.loginAminer(driver)

        # 重复点击查看全部和加载更多
        try:
            i = 0
            time.sleep(self.sleeptime)  # 给网页足够的加载时间
            while driver.find_element_by_xpath('//*[@class="menu_paper"]//*[@class="more_paper"]/span'):
                time.sleep(self.sleeptime * 0.5)  # 等待网页加载好之后才能点击"加载更多"
                more_paper = driver.find_element_by_xpath('//*[@class="menu_paper"]//*[@class="more_paper"]/span')
                driver.execute_script("arguments[0].click();", more_paper)
                # more_paper.click()
                i += 1
                # print(i)
        except Exception:
            # 不能再点击加载更多按钮时，执行以下操作
            paper_name_list = object()
            try:
                time.sleep(self.sleeptime)
                if driver.find_element_by_css_selector('[class="a-aminer-components-pub-publication-list'
                                                       '-aminerPaperList profliePaperList '
                                                       'publication_list"]'):
                    # 获取论文列表
                    paper_name_list = self.get_paper_list(driver)
                    if len(paper_name_list) == 20:
                        # 可能是点击加载更多失败，跳转到异常
                        if count != 1:
                            print("20?")
                            print("异常" + i)
            except Exception:
                # 发生异常，再次尝试获取论文列表
                print("exception")
                time.sleep(self.sleeptime)
                # driver.close()
                paper_name_list = self.parse_paper_list(profile_url, driver, interval, 1)
        driver.close()
        return paper_name_list

    def parse_paper_list_loop(self, profile_url, driver, interval):
        # 获取作者论文全部论文信息
        count = 0
        paper_list = self.parse_paper_list(profile_url, driver, interval, count)
        if len(paper_list) == 0:
            # 获取的论文列表未空，则再次尝试
            # print("len(paper_list)==0?_______________________")
            count += 1
            while count <= 2:
                # 至多尝试3次
                paper_list = self.parse_paper_list(profile_url, driver, interval, count)
                if len(paper_list) > 0:
                    # 论文列表成功获取，break
                    break
                count += 1
        return paper_list

    def get_paper_list(self, driver):
        # 解析，获得最终的作者论文列表，格式是论文名称+论文所有作者列表
        paper_list = []
        paper_list_element = driver.find_element_by_css_selector('[class="a-aminer-components-pub-publication-list'
                                                                 '-aminerPaperList profliePaperList '
                                                                 'publication_list"]').get_attribute('innerHTML')
        # print(paper_list_element)
        paper_list_html = etree.HTML(paper_list_element)
        paper_divs = paper_list_html.xpath('//div[@class="paper-item '
                                           'a-aminer-components-pub-c-publication-item-paperItem"]')
        if len(paper_divs) == 0:
            # 此处是解决问题：有些页面的html元素class不同
            paper_divs = paper_list_html.xpath('//div[@class="paper-item '
                                               'a-aminer-components-pub-c-publication-item-paperItem end"]')
        co_authors = []
        print(len(paper_divs))
        if len(paper_divs) > 0:
            # 有论文，进行解析
            for item in paper_divs:
                # 论文名称
                paper_name = item.xpath('div[1]/div[1]/div/a/span/span/span/text()')
                # 论文所有作者
                all_span = item.xpath('div[1]/div[2]/div/div/span')
                authors = []
                for span in all_span:
                    author = span.xpath('span[1]/span/a[@class="author_label"]/span/text()')
                    if len(author) == 0:
                        author = span.xpath('span[1]/span[1]/span/span[@class="author_label"]/span/text()')
                    # print(author)
                    try:
                        authors.append(author[0])
                    except Exception:
                        pass
                try:
                    paper_list.append([paper_name[0], authors])
                except Exception:
                    pass
        return paper_list


def download_imgs(src_dict, theme, file_count):
    # 下载作者图片
    for img_dict in src_dict:
        name = img_dict['name']
        src = img_dict['img_src']
        img_suffix = src[src.rfind('.'):]
        img_get = requests.get(src)
        dir_path = 'D:/Code/PycharmProjects/aminerCrawl/img/' + theme + "/" + str(file_count)
        create_dir_not_exist(dir_path)
        with open(dir_path + "/" + name + img_suffix, 'wb') as f:
            f.write(img_get.content)


def create_dir_not_exist(path):
    if not os.path.exists(path):
        os.makedirs(path)


def dump_to_json_file(author_infos, theme, file_count):
    # 写json
    Author_dict = {theme: author_infos}
    jsObj = json.dumps(Author_dict)
    fileObject = open('json/ResultOf_' + theme + '_' + str(file_count) + '.json', 'w', encoding='utf-8')
    fileObject.write(jsObj)
    fileObject.close()


def get_headless_webdriver():
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    driver = webdriver.Chrome(executable_path='driver/chromedriver.exe', options=option)
    return driver


if __name__ == "__main__":
    driver = get_headless_webdriver()
    theme = 'data mining'  # 搜索领域的关键词
    spider = AminerSpider(theme=theme, driver=driver)
    spider.parse()
