#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-07-30 17:21:55
# @Author  : Artio (499722757@qq.com)
# @Link    : http://github.com/luopeixiong
# @Version : $Id$

import requests
from scrapy import Selector
import execjs
import re
import urllib.parse

class PbcCookie:
    def __init__(self, cookies={}):
        self.cookies = cookies
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
          'Accept-Encoding': 'gzip, deflate',
          'Accept-Language': 'zh-CN,zh;q=0.8',}
        
    
    def first(self, url):
        # 初始化页面
        self._res =  requests.get(url,headers=self.headers)
        self.cookies.update(self._res.cookies.get_dict())
        return self._res
    
    def js_read(self, res):
        # 重构js return eval执行js代码
        return "function js(){var str=\"\";%s;return str}" % Selector(res).xpath('//script/text()').extract_first().replace("eval","str+=", 1)
    
    def js_read2(self, js_script):
        # 重构js代码 获取 2个cookie片段 以及 跳转url
        js_script = js_script.replace('document.cookie','document.cookie1',1)
        return """
            function js(){
            var window = {innerWidth: 939,innerHeight:637,screenX:0,screenY:0,screen:{width:1366,height:768}};
            var document = {documentElement:{clientWidth:939,clientHeight:637},body:{clientWidth:939,clientHeight:637}};
            %s
            return {cookie:document.cookie,url:window.location,cookie1:document.cookie1}
            }""" % js_script
    
    def js_eval(self, js_script):
        # js渲染
        return execjs.compile(js_script).call('js')
    
    def run(self, url):
        # 获取cookie逻辑
        res = self.first(url)
        js_script = self.js_read(res)
        result = self.js_eval(self.js_read2(self.js_eval(js_script)))
        self.update_cookie(result)
        self._localurl = urllib.parse.urljoin(url,result['url'])
        return self.cookies, self._localurl
    
    def update_cookie(self,result):
        # 更新cookie
        match = re.compile('(.+)=(.+);').search(result['cookie'])
        self.cookies[match.group(1)] = match.group(2)
        match = re.compile('(.+?)=(.+);').search(result['cookie1'])
        self.cookies[match.group(1)] = match.group(2)
    
    def __call__(self, url):
        # 若有cookie 尝试直接获取页面 
        cookies=self.cookies
        if cookies:
            res = requests.get(url,cookies=self.cookies,headers=self.headers)
            res.encoding = res.apparent_encoding
            if 'wzwstemplate' not in res.text:
                # 防止cookie失效
                return res
        # 获取
        cookies, url = self.run(url)
        res = requests.get(url, cookies=cookies, headers=self.headers)
        res.encoding = res.apparent_encoding
        while 'http://1.1.1.2:89' in res.text:
            # flush.js
            res = requests.get(url, cookies=cookies, headers=self.headers)
            res.encoding = res.apparent_encoding
        return res


if __name__ == '__main__':
    url = 'http://www.pbc.gov.cn/zhengwugongkai/127924/128041/2951606/1923625/1923629/d6d180ae/index3.html'
    obj = PbcCookie()
    res = obj(url)
    print(res.text)
    url = 'http://www.pbc.gov.cn/zhengwugongkai/127924/128041/2951606/1923625/1923629/d6d180ae/index1.html'
    res = obj(url)
    print(res.text)