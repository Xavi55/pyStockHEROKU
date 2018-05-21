# -*- coding:utf-8 -*-
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import nltk
nltk.download('punkt')

def feels(stock):
	base='https://www.reuters.com/'
	url=requests.get(base+'/finance/stocks/overview/'+stock)
	doc=BeautifulSoup(url.content,'html.parser')
	links=doc.find_all('div',{'class':'feature'})

	array=[]
	#articles={'good':[],'bad':[],'source':[]}
	pos=0
	neg=0
	good=[]
	bad=[]
	rate=""

	for i,link in enumerate(links):
		if i%3==0:
			inner=link.a.get('href')
			url2=requests.get(base+inner)
			page=BeautifulSoup(url2.content,'html.parser')
			article=page.find('div',{'class':'body_1gnLA'}).text
			caption=page.find('span',{'class':'caption_KoNH1'})#remove pics
			if caption != None:
				article=article.replace(caption.text,'')
			print ('Searching in article #:%s'%(i)) #article number on page
			cut=article.find('-')+2
			sentences=TextBlob(article[cut:]).sentences #frag article into sentences
			
			if sentences == []:
				continue
			
			for sentence in sentences[:-1]:#ignore author stamp
				#print sentence
				#print sentence.sentiment
				#print
				
				if sentence.sentiment.polarity >.3 or .1<sentence.sentiment.polarity<.3 and sentence.sentiment.subjectivity<.46:
					#print sentence
					pos=pos+1
					good.append(str(sentence))#.decode(encoding='ascii',errors='ignore')

#<.3
				elif sentence.sentiment.polarity < -1 or sentence.sentiment.subjectivity<.3 :
					#print sentence
					neg=neg+1
					bad.append(str(sentence))#.decode(encoding='ascii',errors='ignore')
		
			#print ('The number of pos sentences was : %s'%(pos))
			#print ('The number of neg sentences was : %s'%(neg))
	
	
			#if True:#pos>neg: 
				#print ('this article was good b/c of : %s '%(good))
				#print
				#print ('this artile was bad b/c of : %s'%(bad))
				#print
				
			'''
			elif pos==neg:
				print ('this article was fair b/c of : %s &\n%s'%(good,bad))
			else:
				print ('this artile was bad b/c of : %s'%(bad))
			'''
			
			array.append([good,bad,base+inner])
			#articles['good'].append(good)
			#articles['bad'].append(bad)
			#articles['source'].append(base+inner)
			
			
			#pos=0
			#neg=0
			good =[]
			bad=[]

	print ('The number of pos sentences was : %s'%(pos))
	print ('The number of neg sentences was : %s'%(neg))
	
	if pos==neg:
		rate= "fair"
	elif pos>neg:
		rate= "good";
	else:
		rate="bad"		
	array.append(rate)
	
	return array
	#return articles
	#print array
#feels('fb')#testing		
