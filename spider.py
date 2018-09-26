#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import re
import string
import sys
import os
import threading
import requests
import queue
import time
import multiprocessing
class spider:
	def __init__(self,path):
		#待分析url 队列
		self.queUrl = queue.Queue()
		#待分析网页内容队列
		self.quePageInfo = queue.Queue()
		#待下载图片url队列
		self.queImg = queue.Queue()
		#待下载音乐队列
		self.queMusic = queue.Queue()
		#保存爬取结果路径		
		self.path = path
		#爬取线程线程
		self.threads = []
		#写文件锁
		self.mu = threading.Lock()
		#初始化下载路径
		self.DownLoadPath()
		self.first = 1

	def WriteFile(self,content):
		if self.mu.acquire(True):
			if self.first == 1:
				f = open(self.path, "w+", encoding="UTF-8")
				self.first = 2
			else:
				f = open(self.path, "a+", encoding="UTF-8")
			f.write(content)
			f.flush()
			self.mu.release()
	
	#提取网页包含链接
	def GetUrl(self,page):
		regular = "href=\"([^\"]*)"
		pattern = re.compile(regular)
		result = pattern.findall(page)
		for i in result:
			self.queUrl.put(i)

	#给定url放入抓取队列
	def SetCapUrlQueue(self,url):
		self.queUrl.put(url)

	#创建图片保存以及音乐下载目录
	def DownLoadPath(self):
		#下载图片目录
		self.pathImg = "./img"
		#下载音乐目录
		self.pathMusic = "./music"
		#音乐下载链接
		self.musicUrl = "http://mp3-cdn2.luoo.net/low/luoo/radio"
		#不存在创建
		isExists=os.path.exists(self.pathImg)
		if not isExists:
			try:
				os.makedirs(self.pathImg)
			except Exception:
				print ("create",self.pathImg,"err")

		isExists=os.path.exists(self.pathMusic)
		if not isExists:
			try:
				os.makedirs(self.pathMusic)
			except Exception:
				print ("create",self.pathMusic,"err")
			
	#获取网页放入队列
	def GetPage(self):
		while not self.queUrl.empty():
			url = self.queUrl.get()
			r = requests.get(url)
			a = [url,r.text]
			self.quePageInfo.put(a)

	#下载图片
	def DownLoadImg(self):
		while True:
			while not self.queImg.empty():
				img = self.queImg.get()
				#文件存在不下载
				path = self.pathImg + "/" + img[1]
				isExists = os.path.exists(path)
				if not isExists:
					try:
						r = requests.get(img[0])
					except Exception:
						print ("get err")
						continue
					else:
						if r.status_code == 200:
							open(path, 'wb').write(r.content)
						else:
							#GET 失败获取五次
							for i in range(0,5):
								r = requests.get(img[0])
								if r.status_code == 200:
									open(path, 'wb').write(r.content)
									break
								time.sleep(2)

			time.sleep(2)
	
	#下载音乐
	def DownLoadMusic(self):
		while True:
			while not self.queMusic.empty():
				music = self.queMusic.get()
				path = self.pathMusic + "/" + music[0] + "/"
				if '/' in music[1]:
					tmp = music[1].split('/')
					filePath = self.pathMusic + "/" + music[0] + "/" + tmp[0] + tmp[1] + ".mp3"
				else:
					filePath = self.pathMusic + "/" + music[0] + "/" + music[1] + ".mp3"
				
				#按期刊创建文件夹
				if self.mu.acquire(True):
					isExists = os.path.exists(path)
					if not isExists:
						os.makedirs(path)
					self.mu.release()
				
				#音乐不存在下载
				isExists = os.path.exists(filePath)
				if not isExists:
					try:
						r = requests.get(music[2])
					except Exception:
						print ("get err")
						continue
					else:
						if r.status_code == 200:
							print ("downLoad",music[2])
							open(filePath, 'wb').write(r.content)
						else:
							#GET 失败获取五次
							for i in range(0,5):
								newUrl = music[2].replace('/0','/')
								print ("redownLoad",newUrl)
								r = requests.get(newUrl)
								if r.status_code == 200:
									open(filePath, 'wb').write(r.content)
									break
								time.sleep(2)

			time.sleep(2)
		
	
	#创建下载音乐线程
	def CreateDownLoadMusicThread(self,num):
		for i in range(0,num):
			t = threading.Thread(target=self.DownLoadMusic,args=())
			self.threads.append(t)

	#创建获取网页信息线程
	def CreateGetPageThread(self,num):
		for i in range(0,num):
			t = threading.Thread(target=self.GetPage,args=())
			self.threads.append(t)
	
	#创建分析网页内容线程
	def CreatePsrPageThread(self,num):
		for i in range(0,num):
			t = threading.Thread(target=self.PsrPage,args=())
			self.threads.append(t)
	
	#创建图片下载线程
	def CreateDownLoadImgThread(self,num):
		for i in range(0,num):
			t = threading.Thread(target=self.DownLoadImg,args=())
			self.threads.append(t)

	#启动线程
	def Run(self):
		for t in self.threads:
			t.setDaemon(True)
			t.start()
		t.join()

	#取出网页内容队列分析
	def PsrPage(self):
		while True:
			while not self.quePageInfo.empty():		
				a = self.quePageInfo.get()
				#提取图片链接
				regular  = "(\<img src=\"(http:\/\/img-cdn2.luoo.net\/pics\/vol\/([^\!]*)![^\"]*))|"
				#提取描述
				regular += "(<meta name=\"description\" content=\"([^\"]*))|"
				#提取音乐主题
				regular += "(<meta name=\"keywords\" content=\"([^\"]*))|"
				#提取期刊编号
				regular += "(vol-number rounded\"\>([^\<]*))|"
				#提取期刊标题
				regular += "(vol-title\"\>([^\<]*))|"
				#提取音乐
				regular += "(trackname btn-play\"\>([^\<]*))"
				pattern = re.compile(regular)
				result = pattern.findall(a[1])
				if len(result)<10:
					continue
				i = 0
				first = 0
				content = a[0] + '\n'
				imgName = ""
				music = ""
				for tmp in result:
					if (i == 0):
						#描述
						content += tmp[4] + '\n'	
					elif (i == 1):
						#音乐主题
						content += "@mark " + tmp[6] + '\n'
					elif (i == 2):
						#期刊编号
						music = str(int(tmp[8]))
						imgName = tmp[8] + ".jpg"
					elif (i == 3):
						#期刊标题
						content += "@vol  " +  music + " " + tmp[10] + '\n'
					elif (tmp[0] != ''):
						first = first + 1
						#第一张图片为封面
						if(first == 1):
							#提取图片链接 图片名称
							img = [tmp[1],imgName]
							self.queImg.put(img)
							content += "@music\n"
					else:
						#音乐名
						content += "      " + tmp[12] + '\n'
						#保存音乐下载链接
						s = tmp[12].split('.')
						path = self.musicUrl + music + "/" + s[0] + ".mp3"
						info = [music,tmp[12],path]
						self.queMusic.put(info)
					i = i + 1
				self.WriteFile(content)
			time.sleep(2)

def worker(num,start,end):
	path = 'result' + str(num) + '.txt'
	Luo = spider(path)
	for i in range(start,end):
		content = "http://www.luoo.net/music/"
		if i < 10:
        		url = content +  "00" + str(i)
		elif i < 100:
        		url = content +  "0" + str(i)
		else:
			url = content + str(i)
		Luo.SetCapUrlQueue(url)

	Luo.CreateGetPageThread(5)
	Luo.CreatePsrPageThread(5)
	Luo.CreateDownLoadImgThread(1)
	Luo.CreateDownLoadMusicThread(1)
	Luo.Run()

#创建进程	
def RunSpider(thread,start,end):
		unit = int((end-start)/thread)
		if unit < 2:		
			p = multiprocessing.Process(target = worker, args=(0,start,end))
			p.start()
		else:
			for i in range(thread):
				if i != thread - 1:
					index = start+unit*(i+1)
				else:
					index = end
				p = multiprocessing.Process(target = worker, args=(i,start+unit*(i),index))
				p.start()

def main():
	print ("截止2018-11-12 共969期")
	num = input ("单期下载输入1 批量下载输入2:")
	if eval(num) == 1:
		start = input("请输入下载期刊:")
		if start.isdigit():
			RunSpider(1,int(start),int(start) + 1)
	elif eval(num) == 2:
		start = input("请输入开始下载期刊:")
		end = input("请输入结束下载期刊:")
		#默认5个进程
		if start.isdigit() and end.isdigit() and int(end) > int(start):
			RunSpider(5,int(start),int(end)+1)
		else:
			print ("输入错误")
			exit()
	else:
		print ("请输入正确的数字")
		exit()

if __name__ == '__main__':
	main()
