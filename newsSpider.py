#网易新闻排行榜：普通新闻五条，科技新闻五条，从1小时前点击排行中随机选取五条
import requests
from lxml import etree
import random

def getPage(url):
    headers={
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Connection':'keep-alive',
        'Host':'news.163.com',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }
    response=requests.get(url,headers=headers).text
    return response

def parse(html):
    page=etree.HTML(html)
    newsDiv=page.xpath("//div[@id='news']/following-sibling::div[1]//div[contains(@class, 'tabContents')]//tr/td/a")
    techDiv=page.xpath("//div[@id='tech']/following-sibling::div[1]//div[contains(@class, 'tabContents')]//tr/td/a")

    result=[None]*10
    newsIndex=[]
    techIndex=[]
    resultIndex=[]
    for i in range(5):
        rad=random.randint(0,9)
        rad2=random.randint(0,9)
        while rad in newsIndex:
            rad=random.randint(0,9)
        while rad2 in resultIndex:
            rad2=random.randint(0,9)
        result[rad2]=newsDiv[rad].text

        newsIndex.append(rad)
        resultIndex.append(rad2)
    
    for i in range(5):
        rad=random.randint(0,9)
        while rad in techIndex:
            rad=random.randint(0,9)
        while rad2 in resultIndex:
            rad2=random.randint(0,9)
        result[rad2]=techDiv[rad].text
        
        techIndex.append(rad)
        resultIndex.append(rad2)
    
    return result
