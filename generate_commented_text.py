# coding=utf-8
import urllib.request
import codecs
from txt2html import str2html
from time import sleep
import json
import os
# 在网址中包括空格会产生问题，故采用URL编码，见：http://www.w3school.com.cn/tags/html_ref_urlencode.html
zh2url = lambda x: str(x.encode("utf-8"))[2:-1].replace(u"\\x",u"%").replace(" ", "%20")
entity2baike = lambda x: "https://baike.baidu.com/item/%s" % zh2url(x)
entitylinking_api = u"http://shuyantech.com/api/entitylinking/cutsegment?q="
avpair_api = "http://shuyantech.com/api/cndbpedia/avpair?q="

def getPage(url):
    try:
        page = urllib.request.urlopen(url)
        sleep(2)
        html0 = page.read()
        return html0
    except:
        print("error at %s" % url)
        return ""

class Txt2annotated_html:
    def __init__(self):
        pass
    def transform(self,inFile,outFile):
        self.inFile = "./input/" + inFile
        self.outFile = "./output/" + outFile
        tmp_str = ""
        self.curr_para = ""
        with codecs.open(self.inFile, "r", "utf-8") as f0:
            ii = 0
            for para in f0:
                para_name = "%s_%d" % (inFile[:inFile.find(".")],ii)
                self.curr_para = para
                annotated_para = self.annotate_paragraph(para,para_name)
                tmp_str += (annotated_para+"\r\n")
                ii += 1
        ret_html = str2html(tmp_str)
        with codecs.open(self.outFile, "w", "utf-8") as f0:
            f0.write(ret_html)
        return ret_html
    def get_entity_linking(self,text,text_name=""):
        if text_name != "" and os.path.exists("./entity_linking/%s.json"%text_name):     # 复用已保存的实体划分、链接数据
            with codecs.open("./entity_linking/%s.json"%text_name,"r","utf-8") as f0:
                data = json.load(f0)
            print(("entity_link: %s.json reused" % text_name))
        else:
            url = entitylinking_api+zh2url(text)
            html0 = getPage(url)
            if html0 == "": return text
            data = json.loads(html0)
            with codecs.open("./entity_linking/%s.json"%text_name,"w","utf-8") as f0:
                json.dump(data,f0)
            print(("entity_link: %s.json fetched" % text_name))
        return data
    def get_avpair(self,entity0):
        if not ("%s.json" % entity0) in os.listdir("./data/"):           # 复用
            url = avpair_api + zh2url(entity0)
            html0 = getPage(url)
            if html0 == "": return None
            json0 = json.loads(html0)
            with codecs.open("./data/%s.json" % entity0, "w", "utf-8") as f0:
                json.dump(json0, f0)
            print(("avpair: %s.json fetched" % entity0))
        else:
            with codecs.open("./data/%s.json" % entity0, "r", "utf-8") as f0:
                json0 = json.load(f0)
            print(("avpair: %s.json reused" % entity0))
        return json0
    def annotate_entity(self,range0,entity_json0,entity0):
        l,r = range0
        origin_entity0 = self.curr_para[l:r]
        #包含括号的名字【即含有别名】无法直接用作URL，只能舍弃括号，取一般的解释，但注释中已经有了准确的实体，不难纠正
        if "（" in entity0:
            entity0 = entity0[:entity0.find("（")]
        if "(" in entity0:
            entity0 = entity0[:entity0.find("(")]
        href0 = entity2baike(entity0)
        annotation = entity_json0["ret"]
        for (attr, v0) in annotation:
            if attr == "DESC":
                annotation = v0
                annotation = str(annotation).replace("\"", "\'")
                break
        annotated = r'<a href="%s" title="%s">%s</a>' % (href0,annotation,origin_entity0)
        return annotated
    def annotate_paragraph(self,text,text_name=""):
        data = self.get_entity_linking(text,text_name)
        ret_text = ""
        l0 = 0
        for range0, entity0 in data["entities"]:
            l,r = range0
            json0 = self.get_avpair(entity0)
            if json0 == None: continue
            if not 'ret' in json0 or len(json0['ret']) == 0:                              # 实体没有信息，不标注
                annotated = self.curr_para[l:r]
            else:
                annotated = self.annotate_entity(range0, json0, entity0)
            ret_text += (self.curr_para[l0:l]+annotated)
            l0 = r
        ret_text += (self.curr_para[l0:])
        return ret_text

if __name__ == "__main__":
    trans = Txt2annotated_html()
    # trans.transform("world_cup1.txt","world_cup1.html")
    trans.transform("technique1.txt", "technique1.html")