# -*- coding:utf-8 -*-
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
#import nltk #heroku stuff
#nltk.download('punkt') #heroku stuff

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
			
			print ('Searching in article #%s'%(i)) #article number on page

			inner=link.a.get('href')
			url2=requests.get(base+inner)
			page=BeautifulSoup(url2.content,'html.parser')
			article=page.find('div',{'class':'StandardArticleBody_body'}).text
			unwanted_text=page.findAll('div',{'class':'Image_caption'})#images have capitions
			for words in unwanted_text:
				article = article.replace(words.text,'')#remove caption
			
			cut=article.find('-')+2
			cut2=article.find('Reporting by')
			article = article[cut:cut2]
			sentences=TextBlob(article).sentences #frag article into sentences
			
			if len(sentences) == 0:
				continue

			for sentence in sentences:
				#print sentence
				#print sentence.sentiment
				#print
				
				if sentence.sentiment.polarity >.3 or .1<sentence.sentiment.polarity<.3 and sentence.sentiment.subjectivity<.46:
					#print sentence
					pos+=1
					good.append(str(sentence))#.decode(encoding='ascii',errors='ignore')

#<.3
				elif sentence.sentiment.polarity < -1 or sentence.sentiment.subjectivity<.3 :
					#print sentence
					neg+=1
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
			#append good sentenees, bad, & the src link

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
	
	#print len(array)
	return array


#test the script
#feels('MMM')