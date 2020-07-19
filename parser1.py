# -*- coding: utf-8 -*-
from urllib.parse import urljoin
import urllib.request as urll
import urllib
import scrapy
import json
import sys
import csv
import re

class PycoderSpider(scrapy.Spider):
	name = "pycoder"
	start_urls = ['https://5karmanov.ru/']
	allowed_domains = ['5karmanov.ru']
	
	def parse(self, response):
		woman_home = urll.urlopen('https://5karmanov.ru/catalog/zhenskaya_kollektsiya/').read().decode('utf-8')
		woman_max_page = re.findall(r'class\=\"dark_link\"\>(\d+)\<\/a\>', woman_home)[-1]
		man_home = urll.urlopen('https://5karmanov.ru/catalog/muzhskaya_kollektsiya/').read().decode('utf-8')
		man_max_page = re.findall(r'class\=\"dark_link\"\>(\d+)\<\/a\>', man_home)[-1]

		#store url's to all offer's pages
		url_store = []
		for i in range(1, int(woman_max_page)+1):
			url_store.append('https://5karmanov.ru/catalog/zhenskaya_kollektsiya/?PAGEN_1={}'.format(i))
		for i in range(1, int(man_max_page)+1):
			url_store.append('https://5karmanov.ru/catalog/muzhskaya_kollektsiya/?PAGEN_1={}'.format(i))

		for url in url_store:
			yield response.follow(url, callback=self.parse_page)
	#parse every page
	def parse_page(self, response):
		for post_link in response.xpath('//a[@class="dark_link option-font-bold font_sm"]/@href').getall():
			#short_link = re.search(r'(.*\/)[^\/]*$', post_link).group(1)
			url = urljoin(response.url, post_link)
			yield response.follow(url, callback=self.parse_item)
	#parse every offer on page
	def parse_item(self, response):
		str_url = str(response.url)
		str_url = re.search(r'(.*\/)[^\/]*$', str_url).group(1)
		text_page = urll.urlopen(response.url).read().decode('utf-8')
		#head info
		shop_info = {'url':'','company':'','currency':''}
		shop_info.update({'url':'https://5karmanov.ru'})
		shop_info.update({'company':'5karmanov'})
		shop_info.update({'currency':[['RUR','1']]})
		#main struct
		product = {}
		product.update({'shop_info':shop_info})
		offer = {'available':'true','picture':'','vendorCode':'','vendor':'5karmanov','name':'','url':'','price':'','param':'','currencyId':'','group_id':'','id':'','categories':''}
		vendor_code = re.search(r'\-\w\w(\d+)\_(\d+)\/$', str_url)
		if vendor_code:
			offer.update({'vendorCode':vendor_code.group(1)})
			offer.update({'group_id':vendor_code.group(1)})
			offer.update({'id':vendor_code.group(2)})

		#add product model

		pagetitle = response.xpath('//*[@id="pagetitle"]/text()').get()
		vn = re.search(r'([A-Za-z ]*)\s([А-Яа-я ]*)', pagetitle)
		offer.update({'vendor':vn.group(1)})
		offer.update({'name':vn.group(2)})

		check = [" ₽"]
		arr = []
		#price = re.search(r'.*price\s*font\-bold\s*font\_mxs\s*\".*data\-value\s*=\s*\"(\d+).*', text_page).group(1)
		price = response.xpath('//span[@class="price_value"]/text()').get()
		if price != None:
			#offer.update({'available':'false'})
			offer.update({'price':price})
		else:
			price = response.xpath('//div[@class="prices_block"]//text()').getall()
			for p in price:
				p = re.sub(r'(\n)+(\t)+','',p)
				if "₽" in p:
					arr.append(p)
			if arr == []:
				offer.update({'price':'skipped'})
			else:
				offer.update({'price':arr[0][:-2]})
				offer.update({'oldprice':arr[1][:-2]})
		#anyway
		offer.update({'currencyId':'RUR'})
		print(response.url)

		pictures = []
		pictures = response.xpath('//a[contains(@class,"product-detail-gallery__link popup_link fancy")]/@href').getall()
		pictures = ["https://5karmanov.ru"+x for x in pictures]
		offer.update({'picture':pictures})

		#find categories
		tags = response.xpath('//span[@class="breadcrumbs__item-name font_xs" and not(contains(.,"Главная")) and '
				'not(contains(.,"Каталог"))]//text()').getall()[:-1]
		offer.update({'categories':tags})

		offer.update({'url':response.url})

		#another way with using a label
		#if response.xpath('//span[contains(@class, "icon stock")]').get():
		#	offer.update({'available':'true'})
		only_in_shop = response.xpath('//span[@class="store_view dotted"]/text()')
		if only_in_shop == "Только в магазинах":
			offer.update({'available':'false'})
		
		#description
		descr = response.xpath('//div[@class="content"]/text()').getall()
		descr_str = ""
		for elem in descr:
			descr_str += elem
		descr_str = re.sub(r'(\n)+(\t)+','',descr_str)
		descr_str = re.sub(r'(\n)+','',descr_str)
		descr_str = re.sub(r'(\t)+','',descr_str)
		if descr_str != "":
			offer.update({"description":descr_str})

		#param section
		param = {}
		#anyway
		param.update({u"Возраст": u"Взрослый"})
		if tags[0] == "Мужская коллекция":
			param.update({u"Пол": u"Мужской"})
		else:
			param.update({u"Пол": u"Женский"})

		#wh = response.xpath('//div[contains(@class,"bx_size")]/ul/li[{}]/@title'.format(li_index))
		ssize = response.xpath('//span[contains(@class,"cnt")]/text()').getall()
		if ssize != []:
			param.update({'sizes':ssize})

		#labels
		if response.xpath('//div[contains(@class, "sticker_novinka")]').get():
			param.update({u"Новинка":"1"})
		if response.xpath('//div[contains(@class, "sticker_khit")]').get():
			param.update({u"Хит":"1"})
		if response.xpath('//div[contains(@class, "sticker_sovetuem")]').get():
			param.update({u"Советуем":"1"})
		if response.xpath('//div[contains(@class, "sticker_aktsiya")]').get():
			param.update({u"Акция":"1"})

		#material
		material = response.xpath('//div[contains(@class, "properties__value darken properties__item--inline")]//text()').get().strip()
		param.update({u"Материал":material})
		
		#Moscow shop's
		#start_frame_cache
		"""
		for shop in in_shops:
			if re.search(r'(Москва).+' ,shop.xpath('.//text()').get()).group(1) == "Москва":
				print("Found")
				shop_number.append(re.search(r'(\d+)\/$', shop.xpath('./@href').get()).group(1))
		in_shops = response.xpath('//div[@class="tab-content"]/div[@id="stores"]/div[@class="stores_tab"]/div[@class="loading_block"]').getall()
		"""
	
		offer.update({'param':param})
		product.update({'offer': offer})
		
		print(json.dumps(product,ensure_ascii=False))