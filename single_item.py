# -*- encoding=utf-8 -*-

class Author(object):
    def __init__(self, name, img, citation, paper_list, theme, department, domain):
        self.name = name
        self.img = img
        self.citation = citation
        self.paper_list = paper_list
        self.theme = theme
        self.department = department
        self.domain = domain

    def print_to_json(self):
        info = {"name": self.name,
                "img_src": self.img,
                "citation": self.citation,
                "paper_list": self.paper_list,
                "department": self.department,
                "domain": self.domain}
        return info

    def get_name(self):
        return self.name
