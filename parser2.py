# -*- coding: utf-8 -*-
import requests
import re
import csv
from bs4 import BeautifulSoup

URL = 'https://5karmanov.ru/contacts/stores/'
title = 'name;working_hours;phone;index;adress'
HEADERS = ''

def get_html(url, params=None):
	r = requests.get(url, headers=HEADERS, params=params)
	return r

def get_content(html):
	soup = BeautifulSoup(html, 'html.parser')
	items = soup.find_all('div', class_='item bordered box-shadow wti')

	for item in items:
		ph_number = item.find('a', class_='black')
		if ph_number != None:
			ph_number = re.sub(r'\+{0,1}(\d)\s\((.*)\)\s(\d{2,3})-(\d{2})-(\d{2})', r'\1\2\3\4\5', ph_number.get_text())
			ph_number = ph_number.replace('(', '')
			ph_number = ph_number.replace(')', '')
		else:
			ph_number = 'shop@5karmanov.ru'
		work_time = item.find('span', class_='text font_xs muted777')
		if work_time != None:
			work_time = work_time.get_text()
		else:
			work_time = 'None'
		info_str = item.find('a', class_='darken').get_text(strip=True)
		#name - g(1), index - g(3), adr - g(4)
		big_title = re.search(r'^([^,]+),\s(([\d]*),)*(.*)', info_str)
		name = big_title.group(1)
		if big_title.group(3) != None:
			index = big_title.group(3)
		else:
			index = "None"
		adr = big_title.group(4)
		str = name+';'+work_time+';'+ph_number+';'+index+';'+adr.strip()
		print(str.strip(' '))

def parse():
	html = get_html(URL)
	if html.status_code == 200:
		print(title)
		get_content(html.text)
	else:
		print('Error')

parse()