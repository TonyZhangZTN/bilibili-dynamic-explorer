import os
import requests
import json
import shutil
from requests.adapters import HTTPAdapter
import re
import difflib
import pymysql
import time, datetime
import random
oldAPIURL = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history"
newAPIURL = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
APIURL = oldAPIURL
debug = False
def quickGet(url,params):
	headers = {
	"User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
	}
	try:
		s = requests.Session()
		s.mount('http://',HTTPAdapter(max_retries=100))#设置重试次数为10次
		s.mount('https://',HTTPAdapter(max_retries=100))
		buffer = s.get(url,params=params,timeout=1, headers = headers)
	except requests.exceptions.ConnectionError as e:
		print("连接超时")
	buffer.encoding="utf-8"
	if debug == True:
		print(buffer.text)
	return buffer.text
#获取一列动态中的最大动态id和时间戳，只用于查找动态id范围用
def findMaxIdAndTime(uid,did):
	#arg={'host_mid':uid,'offset':did+1,'timezone_offset':-480}
	arg={'host_uid':uid,'offset_dynamic_id':did+1}
	js = json.loads(quickGet(APIURL,arg))
	if 'cards' in js['data']:
		return js['data']['cards'][0]['desc']['dynamic_id'],js['data']['cards'][0]['desc']['timestamp']
	else:
		return -1,-1
#获取顶层动态ID
def getTopId(uid):
	#arg={'host_mid':uid,'timezone_offset':-480}
	arg={'host_uid':uid}
	js = json.loads(quickGet(APIURL,arg))
	if 'cards' in js['data']:
		return js['data']['cards'][0]['desc']['dynamic_id']
	else:
		return -1
def printFromBackToFront(uid,frontId,backId,filename):#打印并保存
	#-480  是GMT+8的意思
	#arg = {'host_mid':uid,'offset':backId+1,'timezone_offset':-480}#之所以+1是因为直接请求这个动态id的返回数据不包含此动态id的内容
	arg = {'host_uid':uid,'offset_dynamic_id':backId+1}#之所以+1是因为直接请求这个动态id的返回数据不包含此动态id的内容
	cnt = 0
	flag = True
	with open(filename,'w',encoding='utf-8') as fo:
		fo.write("<html><head><title>"+filename+"</title><head/><body>")
		while flag == True:
			sleepTime = 0.45 + random.random()/10
			time.sleep(sleepTime)
			data = json.loads(quickGet(APIURL,arg))
			print(data)
			print("sleepTime:" + str(sleepTime))
			if 'cards' in data['data']:
				for i in data['data']['cards']:
					if i['desc']['dynamic_id']<frontId:
						flag = False
						break
					cnt += 1
					fo.write("<hr><p>"+'倒数第'+str(cnt)+'条动态'+"</p>")
					print('倒数第'+str(cnt)+'条动态')
					fo.write("<p>"+'日期:'+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['desc']['timestamp']))+"</p>")
					print('日期:'+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i['desc']['timestamp'])))
					fo.write("<p>"+'<a href=\"https://t.bilibili.com/'+str(i['desc']['dynamic_id'])+"\">动态url</a></p>")
					print('动态id:'+str(i['desc']['dynamic_id']))
					#print('type:'+str(i['desc']['type']))
					arg['offset_dynamic_id'] = i['desc']['dynamic_id']
					if i['desc']['type'] == 1:#转发
						#print('orig_type:'+str(i['desc']['orig_type']))
						tmp = json.loads(i['card'])
						fo.write("<p>"+'用户:'+tmp['user']['uname']+"</p>")
						print('用户:'+tmp['user']['uname'])
						fo.write("<p>"+'转发内容:\n'+tmp['item']['content']+"</p>"+"<div style=\"background-color:rgb(128,128,128);\">")
						print('转发内容:\n'+tmp['item']['content'])
						if 'origin' in tmp:
							tmp = json.loads(tmp['origin'])
						else:
							fo.write(tmp['item']['tips'])
							print(tmp['item']['tips'])
						if i['desc']['orig_type'] == 2:
							fo.write('原相册:\n'+tmp['item']['description']+"<br><p>")
							print('原相册:\n'+tmp['item']['description'])
							for j in tmp['item']['pictures']:
								fo.write("<img src=\""+j['img_src']+"@100w_100h_1e_1c.webp\" width=\"100px\" height=\"100px\"/>")
							fo.write("<p><br>")
						elif i['desc']['orig_type'] == 4:#正文
							fo.write('正文:\n'+tmp['item']['content'])
							print('正文:\n'+tmp['item']['content'])
						elif i['desc']['orig_type'] == 8:#视频
							fo.write('视频:\n'+tmp['title']+'<br>描述:\n'+tmp['desc'])
							print('视频:\n'+tmp['title']+'描述:\n'+tmp['desc'])
						elif i['desc']['orig_type'] == 64:#专栏
							fo.write('专栏:\n'+tmp['title'])
							print('专栏:\n'+tmp['title'])
						fo.write("</div>")
		
					elif i['desc']['type'] == 2:#图文
						tmp = json.loads(i['card'])
						fo.write("<p>"+'图文:\n'+tmp['item']['description']+"</p><br><div>")
						for j in tmp['item']['pictures']:
							fo.write("<img src=\""+j['img_src']+"@100w_100h_1e_1c.webp\" width=\"100px\" height=\"100px\"/>")
						fo.write("</div><br>")
						print('图文:\n'+tmp['item']['description'])
					elif i['desc']['type'] == 4:#正文
						tmp = json.loads(i['card'])
						fo.write("<p>"+'正文:\n'+tmp['item']['content']+"</p>")
						print('正文:\n'+tmp['item']['content'])
					elif i['desc']['type'] == 8:#视频
						tmp = json.loads(i['card'])
						fo.write("<p>"+'视频:\n'+tmp['title']+'描述:\n'+tmp['desc']+"</p>")
						print('视频:\n'+tmp['title']+'描述:\n'+tmp['desc'])
					elif i['desc']['type'] == 64:#专栏
						tmp = json.loads(i['card'])
						fo.write("<p>"+'专栏:\n'+tmp['title']+"</p>")
						print('专栏:\n'+tmp['title'])
					print("\n\n")
			else:
				break
		fo.write("</body>\n</html>\n")
		fo.close()

def findBottomId(uid,end):
	cnt = 0
	l = 1 #没有动态id是1的动态，当成最小值
	r = end # 传入topId，最大id
	bottomId = -1 #默认id为-1，即异常
	while l<=r:
		sleepTime = 0.45 + random.random()/10
		time.sleep(sleepTime)
		m = (l+r)//2
		cnt = cnt + 1
		mid,mt = findMaxIdAndTime(uid,m)#如果无就是-1
		#*mid<=m，有m不一定存在mid,不能直接从找到的mid缩小范围，否则可能漏*
		print("findBottomId")
		print('depth'+str(cnt) +"sleepTime:" + str(sleepTime))
		print("l=%d\nr=%d\nm=%d"%(l,r,m))
		print("mid="+str(mid)+'\n\n')
		if mid>0 :
			bottomId = mid
			r = m - 1
		else:
			l = m + 1
	return bottomId
#找时间大于等于frontTime的第一个动态id
#--------------------------------------------------------------------
#                 | did   
#Front            |  mt                                          Back
#            front|time
#--------------------------------------------------------------------
def findFrontId(uid,fronttime,l,r):
	cnt = 0
	frontId = l
	while l<=r:
		sleepTime = 0.45 + random.random()/10
		time.sleep(sleepTime)
		m = (l+r)//2
		cnt = cnt + 1
		mid,mt = findMaxIdAndTime(uid,m)
		print("findFrontId")
		print('depth'+str(cnt)+"sleepTime:" + str(sleepTime))
		print("l=%d\nr=%d\nm=%d"%(l,r,m))
		print("mid="+str(mid))
		if mt > 0:
			print("time:"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mt))+'\n\n')
			if mt>=fronttime :
				frontId = mid
				r = m - 1
			else:
				l = m + 1
		else:
			r = m - 1
	return frontId
#找时间小于等于backTime的第一个动态id
def findBackId(uid,backtime,l,r):
	cnt = 0
	backId = r
	while l<=r:
		sleepTime = 0.45 + random.random()/10
		time.sleep(sleepTime)
		m = (l+r)//2
		cnt = cnt + 1
		mid,mt = findMaxIdAndTime(uid,m)
		print("findBackId")
		print('depth'+str(cnt)+"sleepTime:" + str(sleepTime))
		print("l=%d\nr=%d\nm=%d"%(l,r,m))
		print("mid="+str(mid))
		if mt > 0:
			print("time:"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mt))+'\n\n')
			if mt<=backtime :
				backId = mid
				l = m + 1
			else:
				r = m - 1
		else:
			l = m + 1
	return backId
def main():
	uid = input("uid:")
	data = json.loads(quickGet("https://api.bilibili.com/x/space/acc/info",{'mid':uid,'jsonp':'jsonp'}))
	print(data)
	filename = data['data']['name']+".html"
	print("user:"+data['data']['name'])
	operation = input("mode\n1:all\t2:range")
	if(operation == "2"):
		timestr = input("begin: YYYY-MM-DD HH:MM:SS\n")
		fronttime = int(time.mktime(time.strptime(timestr, "%Y-%m-%d %H:%M:%S")))

		timestr = input("till when?: YYYY-MM-DD HH:MM:SS\n")
		backtime = int(time.mktime(time.strptime(timestr, "%Y-%m-%d %H:%M:%S")))
	topId = getTopId(uid)
	bottomId = 1
	if topId == -1:#l
		print("此人无动态")
		exit()
	else:
		bottomId = findBottomId(uid,topId)
		#print('第一个动态id:'+str(bottomId))
	if(operation == "1"):
		frontId = bottomId
		backId = topId
	elif(operation == "2"):
		frontId = findFrontId(uid,fronttime,bottomId,topId)
		backId = findBackId(uid,backtime,bottomId,topId)
		#print("范围内最早id%d，最晚id%d"%(frontId,backId))
	printFromBackToFront(uid,frontId,backId,filename)
if __name__ == '__main__':
	main()