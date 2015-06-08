'''
Created on May 4, 2015
@author: uday
'''
import requests,json
from bs4 import BeautifulSoup
from urllib.request import urlopen
from TwitterSearch import *
from alchemyapi import AlchemyAPI
from pws import Google
import csv
import numpy as np
import matplotlib.pyplot as plt
import facebook
import persona_util as pu
from TwitterSearch.TwitterSearchOrder import TwitterSearchOrder
from datetime import date, timedelta

def readFacebookPosts(facebookHandle):
    APP_ID = "@@@"
    APP_SECRET = "$$$"
    posts=[]
    graph_url = "https://graph.facebook.com/"
    user_page = graph_url + facebookHandle
    post_args = "/posts/?key=value&access_token=" + APP_ID + "|" + APP_SECRET
    post_url = user_page + post_args
    print(post_url)
    resp = requests.get(post_url)
    response = json.loads(resp.text)
    fb_posts = response['data']
    
    for post in fb_posts:
        try:
            posts.append(post["message"])
            print(post["message"])
        except:
            print("key error")
    return posts

def searchGoogle(keyword):
    response = Google.search_news(keyword,num=5,start=2)
    results = response['results']
    links = [result['link'] for result in results]
    return links

def getTweets(username):
    tFeeds=[]
    try:
        #tuo = TwitterUserOrder(username) # create a TwitterUserOrder
        tso = TwitterSearchOrder() # create a TwitterSearchOrder object
        tso.set_keywords([username])
        tso.set_language('en')
        tso.set_count(50)
        tso.set_include_entities(False)
        tso.set_until(date.today()-timedelta(days=2))

        # it's about time to create TwitterSearch object
        ts = TwitterSearch(
            consumer_key = '%%%',
            consumer_secret = '^^^',
            access_token = '&&&',
            access_token_secret = '@@@'
        )

        # start asking Twitter
        counter=0
        for tweet in ts.search_tweets_iterable(tso):
            if (counter==300):
                break
            tweetx=str(tweet['text'].encode('ascii', 'ignore'))
            counter=counter+1
            tFeeds.append(tweetx)
            
    except TwitterSearchException as e: # catch all those ugly errors
        print(e)
        
    return tFeeds

def performSA(pname, text):
    alchemyapi = AlchemyAPI()
    response = alchemyapi.sentiment('text', text)
    sentiment = response['docSentiment']
    if (sentiment['type']=='neutral'):
        sentiment['score']='0'
    return sentiment

def performEE(url):
    alchemyapi = AlchemyAPI()
    response = alchemyapi.entities('url', url)
    relatedEntities = {}
    if response['status'] == 'OK':
        entities = response['entities']
        for entity in entities:
            if (float(entity['relevance'])>0.1):
                relatedEntities[entity["type"]]=entity["text"]
    return relatedEntities

def performCT(url):
    conceptText=[]
    alchemyapi = AlchemyAPI()
    response = alchemyapi.concepts('url', url)
    if response['status'] == 'OK':
        concepts = response['concepts']
        for concept in concepts:
            if (float(concept['relevance'])>0.1):
                conceptText.append(concept['text'])
    return conceptText

def performKeywordExtraction(text):
    keywordText=[]
    alchemyapi = AlchemyAPI()
    response = alchemyapi.keywords("text", text)
    if response['status'] == 'OK':
        keywords = response['keywords']
        for keyword in keywords:
            if (float(keyword['relevance'])>0.1):
                keywordText.append(keyword['text'])
    return keywordText    
    
def consolidateConcepts(pname):
    links=searchGoogle(pname)
    linkX=[]
    concepts=[]
    for link in links:
        index = link.find("&sa")
        if (index!=-1):
            concepts.extend(performCT(link[0:index]))
        else:
            concepts.extend(performCT(link))
    return concepts
    
def performSAURL(pname, url, tData):
    response = urlopen(url)
    html = response.read()    
    soup = BeautifulSoup(html)
    text = str(soup.get_text().encode('latin-1', 'ignore'))
    text = text + "." + ''.join(tData)
    return performSA(pname, text)

def performPIURL(pname, url,tData):    
    response = urlopen(url)
    html = response.read()    
    soup = BeautifulSoup(html)
    text = str(soup.get_text().encode('latin-1', 'ignore'))
    text = text + "." + ''.join(tData)
    traits, needs, values = performPI(pname, text)
    return traits, needs, values

def performPI(pname, text):
    traits = {}
    needs  = {}
    values = {}
    
    username = ""
    password = ""
    url      = "https://gateway.watsonplatform.net/personality-insights/api/v2/profile"
    resp = requests.post(url, auth=(username, password),  headers = {"content-type": "text/plain"}, data=text)
    response = json.loads(resp.text)
    tree = response['tree']
    
    traitsFromResponse = tree['children'][0]['children'][0]['children'][0]['children']
    for trait in traitsFromResponse:
        traits[trait['id']]=trait['percentage']

    needsFromResponse = tree['children'][1]['children'][0]['children']
    for need in needsFromResponse:
        needs[need['id']]=need['percentage']

    valuesFromResponse = tree['children'][2]['children'][0]['children']
    for value in valuesFromResponse:
        values[value['id']]=value['percentage']   

    return traits, needs, values
    
def processPersona(person):
    name = person[0]
    wiki = person[1]
    twitterUserName = person[2]
    facebookHandle = person[3]
    
    if twitterUserName!="NA":
        twitterData = getTweets(twitterUserName)
        sentiment=performSA(name,twitterData)
    else:
        twitterData = ["no twitter data"]
        sentiment={'type': 'NA', 'score': 'NA', 'mixed':'NA'}
        
    if facebookHandle!="NA":
        posts = readFacebookPosts(facebookHandle)
        posts_text = " ### " + ''.join(posts)
    else:
        posts_text = (name+" , "+" Private Facebook Account; ") * 50
    
    if (wiki!="NA"):
        traits, needs, values = performPIURL(name, wiki,twitterData)
        relatedEntities = performEE(wiki)
    else:
        traits, needs, values = {"no data":"no data"}
        relatedEntities = {"no data":"no data"}
       
    concepts = consolidateConcepts(name)
    keywords = performKeywordExtraction(posts_text)
    
    filename=name.replace(" ","_").lower()
    
    pu.wordCloud(filename, "keywords", str(keywords).strip('[]'))
    pu.wordCloud(filename, "concepts", str(concepts).strip('[]'))
    pu.entityNetwork(name, filename, relatedEntities)
    pu.dotplot(name, filename, traits, "traits", "traits")
    pu.dotplot(name, filename, needs, "needs", "needs")
    pu.dotplot(name, filename, values, "values", "values")
    print("score for "+name+" "+computeSPS(traits, values, sentiment))
    
def createPersonas(filename):
    f = open(filename, 'rt')
    try:
        persons = csv.reader(f)
        counter=0
        for person in persons:
            if (counter>0):
                processPersona(person)
            counter+=1
    finally:
        f.close()

def computeSPS(traits, values, sentiment):
    tvalues = [int(float(value)*100) for name, value in traits.items()]
    vvalues = [int(float(value)*100) for name, value in values.items()]
    ss=0
    if (sentiment['type']!='NA'):
        ss=int(float(sentiment['score'])*100)
        print(sentiment['score'])
    total=0
    for tvalue in tvalues:
        total+=tvalue
    for vvalue in vvalues:
        total+=vvalue
    total+=ss
    return str(int(total*2/3))
    
if __name__ == '__main__':
    person=[]
    person.append("Robert Griffin")
    person.append("http://en.wikipedia.org/wiki/Robert_Griffin_III")
    person.append("RGIII")
    person.append("RG3")
    processPersona(person)