# -*- coding:utf-8 -*-
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
#import nltk #heroku stuff
#nltk.download('punkt') #heroku stuff

def feels(stock):
	base='https://www.reuters.com'
	url=requests.get(base+'/companies/'+stock+'/news')
	doc=BeautifulSoup(url.content,'html.parser')
	news=doc.find_all('div',{'class':'FeedScroll-feed-container-106s7'})
	if not len(news):
		print('No articles were found')
		return [['No articles were found','No articles were found','https://www.reuters.com'],['UNKWN']]
	else:
		items=news[0].find_all('div',{'class':'item'})[:7]
		links={}
		for item in items:
			try:
				if links[item.a.get_text()]:
					continue		
			except KeyError as e:
				links[item.a.get_text()]=item.a.get('href')
					#print(item.a.get('href'),item.a.get_text())
	####
	##
	#
		array=[]##[[good sentences , bad sentences , src link] , ['rating']]
		pos=0
		neg=0
		good=[]
		bad=[]
		rate=""

		for link in links:
			#print ('Searching in : %s'%(link))
			url2=requests.get(links[link])
			page=BeautifulSoup(url2.content,'html.parser')
			article=page.find('div',{'class':'StandardArticleBody_body'}).text
			unwanted_text=page.findAll('div',{'class':'Image_caption'})#images have capitions
			for words in unwanted_text:
					article = article.replace(words.text,'')#remove caption
			
			cut=article.find('-')+2
			cut2=article.find('Reporting by')
			article = article[cut:cut2]
			sentences=TextBlob(article).sentences #frag article into sentences
			
			if len(sentences)==0:
				continue
			
			for sentence in sentences:
				#print(sentence,'::',sentence.sentiment)

				if sentence.sentiment.polarity >.3 or .1<sentence.sentiment.polarity<.3 and sentence.sentiment.subjectivity<.46:
					#print sentence
					pos+=1
					good.append(str(sentence))#.decode(encoding='ascii',errors='ignore')

#<.3
				elif sentence.sentiment.polarity < -1 or sentence.sentiment.subjectivity<.3 :
					#print sentence
					neg+=1
					bad.append(str(sentence))#.decode(encoding='ascii',errors='ignore')
			array.append([good,bad,links[link]])
			good=[]
			bad=[]
		#print ('The number of pos sentences was : %s'%(pos))
		#print ('The number of neg sentences was : %s'%(neg))
		
		if pos==neg:
			rate= "fair"
		elif pos>neg:
			rate= "good";
		else:
			rate="bad"		
		array.append(rate)
		return array
###testing
#feels('MMM')

