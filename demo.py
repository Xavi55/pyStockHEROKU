# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from flask import jsonify

import json
import re

import pandas as pd
import numpy as np
import pandas_datareader.data as web
from datetime import datetime

import pygal
from pygal.style import DarkStyle

import sent #other file

#import locale
#locale.setlocale(locale.LC_ALL,'') #use conventional number formatting
app=Flask(__name__)
app.config['SECRET_KEY'] = 'omega001'
socketio = SocketIO( app )
class stock:
	def __init__(self,name):
		self.name=name
		
	def getName(self):
		url=requests.get('http://quotes.wsj.com/'+self.name+'/financials/annual/income-statement')
		dom=BeautifulSoup(url.content, "html.parser")
		data=dom.find('h1')
		while True:
			try:
				tik=data.find('span',{'class':'tickerName'}).text
				co=data.find('span',{'class':'companyName'}).text
				ex=data.find('span',{'class':'exchangeName'}).text.replace('(','').replace(')','')
			except AttributeError:
				#print "Retrying..."
				#pass
				continue
			return tik+' '+co+' '+' '+ex
		#data=dom.find('div',{'class','cr_quotesHeader'})
		#print data
		#name=data.find('span').text
		#print name
		#name=re.sub('[()]','',name).#remove parentheses
		#return name
	
	def getPrices(self):
		url=requests.get('http://quotes.wsj.com/'+self.name+'/financials/annual/income-statement')
		page=BeautifulSoup(url.content, "html.parser")
		array=[]
		while True:
			try:
				array.append(float(page.find(id='quote_val').text.replace(',','')))
				array.append(page.find('li',{'class':'crinfo_diff'}).text)
				array.append(page.find_all('span',{'class':'data_data'})[5].text)
			except AttributeError:
				#print "...Retrying"
				continue
				#pass
			return array
		#array.append())#round it?
		#array.append()
		#array.append()
		#return [1,2,3]
		#return array
		
		#gathers financial data as of most recent quarter(s)
	def getFin(self):
		#income statement data
		url=requests.get('http://quotes.wsj.com/'+self.name+'/financials/quarter/income-statement')
		incPage=BeautifulSoup(url.content, "html.parser")
		#data=dom.find_all('tbody')[1].find_all('td')
		#data=dom.find('table',{'class':'cr_dataTable'}).find_all('td')
		data=incPage.find('td',string='EPS (Basic)').find_next_siblings("td")
		eps=0
		#check for negative values
		for k in data[:4]:
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
		pe=round((float(price)/float(eps)),2)
		if pe<0:
			pe='NEG'
		
		#balance sheet data
		url2=requests.get('http://quotes.wsj.com/'+self.name+'/financials/quarter/balance-sheet')
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
		de=round(liab/equity,2)		
		pb=round((float(price)/(equity/shares)),2)
		array=[CAP,eps,pe,de,pb]
		#print array
		return array
		
	def getComp(self):
		url=requests.get('http://quotes.wsj.com/'+self.name)
		fPage=BeautifulSoup(url.content, "html.parser")
		tik=fPage.find(id='cr_competitors_table').find_all('h5')
		name=fPage.find(id='cr_competitors_table').find_all('h4')
		
		array=[]
		#test=[]
		for i in range(0,len(tik))[:3]:	#first 3 counts in range
			array.append([tik[i].text,name[i].text])	#append ( array+array ) = 2d array/list
		'''
		for i in tik[:3]:
			array.append(i.text)
		'''
		return array
		
	def getSent():
		return 1	
#---------------

@app.route('/')
def index():
	return render_template('stock.html')
#---------------
@socketio.on('get')#fetches static data i.e mkCap. p/e ratio 
def get(name):
	print '\n============'
	print"Processing "+name['sym']
	print'=============\n'
	x=stock(name['sym'])
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
	
	conv=lambda x:x/x[0]
	diff=datetime.today().year-1
	start=datetime.today().replace(year=diff)#one year ago	
	end=datetime.today()
	x=stock(n['sym'])
	comp=x.getComp()#retrieve competition
	data=web.DataReader(str(n['sym']).upper(),'robinhood',start,end)##must uppercase stock tik?
	
	debut=float(data['close_price'][0])#determine if stock has grown last year
	fin=float(data['close_price'][-1])
	
	if fin > debut:
		rate="grown"
	else:
		rate="fell"
	
	data=conv(data['close_price'].astype('float64'))
	line_chart=pygal.Line(height=400,style=DarkStyle)
	line_chart.title='Performance Since Last Year'
	line_chart.x_title='Days'
	line_chart.y_title='% Change'
	line_chart.x_labels=data.reset_index()['begins_at']#label x-axis by dates
	line_chart.add(n['sym'], data)
	for i in comp:
		#print i
		try:
			s=web.DataReader(str(i[0]),'robinhood',start,end)
			s=conv(s['close_price'].astype('float64'))
			line_chart.add(i[1],s)
		except:
			pass
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

if __name__=='__main__':
	socketio.run(app)
