# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

import json
from collections import OrderedDict

from flask import jsonify

import json
import re
""" 
import pandas as pd
import numpy as np
import pandas_datareader.data as web
"""
from datetime import datetime
import pygal
from pygal.style import DarkStyle

import sent #other file

#import locale
#locale.setlocale(locale.LC_ALL,'') #use conventional number formatting
app=Flask(__name__)
app.config['SECRET_KEY'] = 'omega001'
socketio = SocketIO( app )

HEADERS={
	'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
	'cache-control': "no-cache",
    'postman-token': "8c88c040-ad4b-852b-905d-6788dfa2929b"
}

class Stock:

	page=None
	def __init__(self,name):
		self.name=name
		url=requests.request('GET','https://www.wsj.com/market-data/quotes/{}'.format(self.name),headers=HEADERS)
		self.page=BeautifulSoup(url.content, "html.parser")

	def isFake(self):#is the stock real
		try:
			data=self.page.find('div',class_='cr_notfound_header module').text
		except AttributeError:
			return 0
		else:
			if 'Not Found' in data:#if it contains these words...
				return 1

	def getName(self):
		head=self.page.find('div',class_='cr_quotesHeader').findAll('span')
		co=head[0].text
		tik=head[1].text
		exch=re.sub(r"(\(|\))",'',head[2].text)#elim parens
		return tik+' '+co+' '+' '+exch
		#data=dom.find('div',{'class','cr_quotesHeader'})
		#print data
		#name=data.find('span').text
		#print name
		#name=re.sub('[()]','',name).#remove parentheses
		#return name
	
	def getPrices(self):
		array=[]#price, %diff, opening price
		array.append(float(self.page.find('span',class_='cr_curr_price').text.replace('$','')))
		array.append(self.page.find('li',class_='crinfo_diff').text)
		array.append(self.page.findAll('ul',class_='cr_data_collection')[1].find('span',class_='data_data').text)
		#print(array)
		return array
		
		#gathers financial data as of most recent quarter(s)
	def getFin(self):
		#income statement data
		url=requests.get('http://quotes.wsj.com/'+self.name+'/financials/quarter/income-statement',headers=HEADERS)
		incPage=BeautifulSoup(url.content, "html.parser")
		#data=dom.find_all('tbody')[1].find_all('td')
		#data=dom.find('table',{'class':'cr_dataTable'}).find_all('td')
		data=incPage.find('td',string='EPS (Basic)').parent.findAll('td')
		
		eps=0
		#check for negative values
		for k in data[1:5]:
			if '(' in k.text:
				eps=eps+-1*float(re.sub('[\(\)]','',k.text))
			else:
				eps=eps+float(k.text)
		eps=round(eps,2)
		price=incPage.find_all('span',{'class':'data_data'})[5].text.replace(',','')
		shares=incPage.find('td',string='Basic Shares Outstanding').find_next_siblings("td")[0].text.replace(',','')
		format=incPage.find('th',{'class':'fiscalYr'}).text
		if "Thousands" in format:
			shares=float(shares)*1000
		else:
			shares=float(shares)*1000000
		
		mCap=float(price)*shares
		if mCap < 1000000000:
			CAP=str(int(mCap/1000000))+"M"
		else:
			CAP=str(int(mCap)/1000000000)+"B"
		pe=round((float(price)/float(eps)),2)#price/earnings
		if pe<0:
			pe='NEG'
		
		#balance sheet data
		"""
		TODO HERE
		recalculate debt/equity?
		"""
		url2=requests.get('http://quotes.wsj.com/'+self.name+'/financials/quarter/balance-sheet',headers=HEADERS)
		balPage=BeautifulSoup(url2.content, "html.parser")	
		liab=balPage.find('td',string='Total Liabilities').find_next_sibling("td").text.replace(',','')
		equity=balPage.find('td',string='Total Equity').find_next_sibling("td").text.replace(',','')#negative equity .. remove parathenses ?
		form=balPage.find('th',{'class':'fiscalYr'}).text
		if "Thousands" in form:
			equity=float(equity)*1000
			liab=float(liab)*1000
		else:
			equity=float(equity)*1000000
			liab=float(liab)*1000000
		de=round(liab/equity,2)#debt/equity
		pb=round((float(price)/(equity/shares)),2)#price/book
		array=[CAP,eps,pe,de,pb]
		#print(array)
		return array
		
	def getComp(self):
		tik=self.page.find(id='cr_competitors_table').find_all('h5')
		name=self.page.find(id='cr_competitors_table').find_all('h4')
		
		array=[]
		#test=[]
		for i in range(0,len(tik))[:4]:	#first 3 comps
			array.append([tik[i].text,name[i].text])	#append ( array+array ) = 2d array/list
		#print(array)
		return array

def getHistory(stockName):
	data = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+stockName+'&outputsize=full&apikey=EOQA5AGR365JSWES')
	data = json.loads(data.text,object_pairs_hook=OrderedDict)['Time Series (Daily)']
		#force organize json

	diff=datetime.today().year-1
	lastYear=datetime.today().replace(year=diff).isoformat()[:10]#one year ago
	start=(data[lastYear]['4. close'])#last years closing price
	cPrice = []#[[dates,closing prices],[...],...]
	c=0
	for date in data:
		if c==252:
			break;
		else:
			cPrice.append([date,(float(data[date]['4. close'])/float(start))])
			c+=1
	cPrice=cPrice[::-1]#reverse list
	#print(cPrice)
	return cPrice
#---------------

@app.route('/')
def index():
	return render_template('stock.html')
#---------------
@socketio.on('get')#fetches static data i.e mkCap. p/e ratio 
def get(name):
	print ('\n=============')
	print("Processing "+name['sym'])
	print('=============\n')
	x=Stock(name['sym'])
	if x.isFake():
		socketio.emit('reply',json.loads(json.dumps({'status':1,'mess':'Not A Real Stock. Try Again!'})))
	else:
		nums= x.getPrices()
		fin=x.getFin()
		post=json.loads(json.dumps({
			'n':x.getName(),
			'p':nums[0],
			'diff':nums[1],
			'op':nums[2],
			'cap':fin[0],
			'eps':fin[1],
			'pe':fin[2],
			'de':fin[3],
			'pb':fin[4]
		}))
		socketio.emit('reply',post)

@socketio.on('fetch')#fetches new prices/data
def get(n):
	x=stock(n['sym'])
	nums=x.getPrices()
	info=json.loads(json.dumps({'n':n['sym'],'p':nums[0],'diff':nums[1]}))
	socketio.emit('update',info)


@socketio.on('chart')#makes charts for each input
def make(n):

	rate=""
	#conv=lambda x:x/x[0]
	#end=datetime.today()
	x=Stock(n['sym'])

	cPrice=getHistory(n['sym'])
	comp=x.getComp()#retrieve competition

	#data=web.DataReader('F','robinhood')
	#data=web.DataReader(str(n['sym']).upper(),'iex',start,end)##must uppercase stock tik?
	#cPrice=cPrice[]#reverse
	#cPrice=cPrice[1]
	start=cPrice[0][1]
	end=cPrice[-1][1]

	#start=float(data['close_price'][0])#determine if stock has grown last year
	#end=float(data['close_price'][-1])

	if end > start:
		rate="grown"
	else:
		rate="fell"

	#data=conv(data['close'])#convert to %Growth
	line_chart=pygal.Line(height=400,style=DarkStyle)
	line_chart.title='Performance Since Last Year'
	line_chart.x_title='Days'
	line_chart.y_title='% Change'
	line_chart.x_labels=map(lambda x:x[0],cPrice)#label x-axis by dates
	line_chart.add(n['sym'],list(map(lambda x:x[1],cPrice)))

	for i in comp:
		#print i
		# try:
		#	s=web.DataReader(str(i[0]),'iex',start,end)
		#	s=conv(s['close_price'])#convert to %Growth
		#	line_chart.add(i[1],s)
		#except:
		#	pass

		closingPrices=getHistory(i[0])
		line_chart.add(i[1],list(map(lambda x:x[1],closingPrices)))	
	img=line_chart.render_data_uri()
	info=json.loads(json.dumps({'n':n['sym'],'chart':img,'perf':rate}))
	socketio.emit('paste',info) 
	
@socketio.on('sentiment')
def get(n):
	x=sent.feels(n['sym'])
	##### need to encode - deode utf-8???
	
	
	#socketio.emit(jsonify(good=x[0],bad=x[1]))
	#x=jsonify(x)
	#print x
	#print(x['bad'][0])
	if x!=None:
		info=json.loads(json.dumps({'n':n['sym'],'data':x}))
		#info=json.loads(json.dumps({'n':n['sym'],'good':x['good'],'bad':x['bad'],'src':x['source']}))
		socketio.emit('sent',info)
	else:
		print("Unable to retrieve News data")
	
#@socketio.on('fin')
#def get(n):
#	x=stock(n['sym'])
#	fin=x.getFin()
#	dat=json.loads(json.dumps({
#	'n':n['sym'],
#	'eps':fin[0],
#	'pe':fin[1],
#	'de':fin[2],
#	'pb':fin[3]
#	}))
#	socketio.emit('nums',dat)

#for testing
#x=Stock('F')
#x.getPrices()
#x.isFake()

if __name__=='__main__':
	socketio.run(app)
