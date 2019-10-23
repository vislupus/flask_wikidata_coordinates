import re
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
	return render_template("index.html")

@app.route('/wiki_table', methods = ['POST'])
def wiki_table():
	if request.method == "POST":
		text_url = request.form['input']
		
		# check if input filed is empty
		if text_url =="":
			return redirect(url_for('index'))
	
	title_list=[]
	wiki_site=[]
	wiki_title=[]
	wiki_url=[]
	wiki_geo={}
	wiki_quick={}
	item={}
	
	if 'wikipedia.org' in text_url:
		p=Path(text_url)
		url="https://"+p.parts[1]

		# Load Wikipedia Category Page
		page_response = requests.get(text_url)
		page_content = BeautifulSoup(page_response.content, "html.parser")

		# check if there is a div tag with class mw-pages or mw-category
		if 'mw-pages' in str(page_content):
			# Pages in category
			divPage = page_content.find('div',{"id":"mw-pages"})
			
			# print("mw-pages")
			
		elif 'mw-category' in str(page_content):
			# Pages in category
			divPage = page_content.find('div',{"class":"mw-category"})
			
			# print("mw-category")
			
		# Get li tags
		li=divPage.find_all('li')
			
		# Looping through all the links
		for j in range(len(li)):
			a=li[j].find('a', href=True)

			# Title of article
			title_list.append(a['title'])
			
			item[a['title']]={}
			item[a['title']]["title"]=a['title']
			
			# Create new link for subpage
			url_new=url+a['href']
			item[a['title']]["title_url"]=url_new
			
			# WikiData from URL
			try:
				page_data = requests.get(url_new)
				page_data_content = BeautifulSoup(page_data.content, "html.parser") 
				li_data=page_data_content.find('li',{"id":"t-wikibase"})
				
				a_data=li_data.find('a', href=True)
				a_data_id=a_data['href'].replace("https://www.wikidata.org/wiki/Special:EntityPage/","")
				a_data_entity="http://www.wikidata.org/entity/"+a_data_id
				
				# Url of wikidata page
				item[a['title']]["wikidata_id"]=a_data_id
				item[a['title']]["wikidata_url"]=a_data_entity
				
				page_data_instance = requests.get(a_data_entity)
				page_data_instance_content = BeautifulSoup(page_data_instance.content, "html.parser") 
				
				# JSON data of a page
				b=str(page_data_instance_content)
				text_json = json.loads(b)
				
				# Whole JSON data of a page
				# print(text_json)
				
				try:
					temp_array_lat=[]
					temp_array_lon=[]
					item[a['title']]['geo']=False
					
					for i in range(len(text_json["entities"][a_data_id]['claims']['P625'])):
						
						# get coordinates from the wikidata page if they exist
						P625_item_lat=text_json["entities"][a_data_id]['claims']['P625'][i]['mainsnak']["datavalue"]["value"]['latitude']
						P625_item_lon=text_json["entities"][a_data_id]['claims']['P625'][i]['mainsnak']["datavalue"]["value"]['longitude']
						
						temp_array_lat.append(P625_item_lat)
						item[a['title']]['latitude']=temp_array_lat
						
						temp_array_lon.append(P625_item_lon)
						item[a['title']]['longitude']=temp_array_lon
						
						# if wikidata has coordinates it become true
						item[a['title']]['geo']=True
				except:
					pass
				
				
				try:
					# get sites from wikidata page
					language_item=text_json["entities"][a_data_id]['sitelinks']
					language_item_keys=language_item.keys()

					listDic = list(language_item.keys())
					# print(listDic)
					
					# n=0
					# if len(listDic)<5:
						# n=len(listDic)
					# else:
						# n=5
						
					# for i in range(n): 
						# key=listDic[i]
						
					for key in listDic:
					# for key in language_item.keys():
						# if (key != 'commonswiki') and ('wikivoyage' not in key) and (key == 'skwiki' or key == 'cswiki' or key == 'eowiki' or key == 'fawiki' or key == 'be_x_oldwiki'):
						if (key != 'commonswiki') and ('wikivoyage' not in key) and ('wikiquote' not in key) and ('wikisource' not in key) and ('wikinews' not in key) and ('wiktionary' not in key) and ('wikiversity' not in key) and ('wikibooks' not in key):
							print(key)
							
							language_title=text_json["entities"][a_data_id]['sitelinks'][key]['title']
							language_url=text_json["entities"][a_data_id]['sitelinks'][key]['url']
							print(language_title)

							wiki_site.append(key)
							wiki_title.append(language_title)
							wiki_url.append(language_url)

							item[a['title']]['wiki_site']=wiki_site
							item[a['title']]['wiki_title']=wiki_title
							item[a['title']]['wiki_url']=wiki_url
							
							# begin scraping data from the pages
							page_coordinates = requests.get(language_url)
							page_coordinates_content = BeautifulSoup(page_coordinates.content, "html.parser")
							
							page_coordinates_content_div=''
							
							# check if there is coordinates on the page
							if ('mw-indicator-coordinates' in str(page_coordinates_content)) and (key != 'cswiki' or key != 'skwiki'):
								page_coordinates_content_div = page_coordinates_content.find('div',{"id":"mw-indicator-coordinates"})
								print("mw-indicator-coordinates")
							
							elif 'coordinatesindicator' in str(page_coordinates_content):
								page_coordinates_content_div = page_coordinates_content.find('span',{"id":"coordinatesindicator"})
								print("coordinatesindicator")
							
							elif ('Показать карту' in str(page_coordinates_content)):
								page_coordinates_content_div = page_coordinates_content.find('span',{"title":"Показать карту"})
								print("Показать карту")
							
							elif 'Xəritədə göstər' in str(page_coordinates_content):
								page_coordinates_content_div = page_coordinates_content.find('span',{"title":"Xəritədə göstər"})
								print("Xəritədə göstər")
							
							elif 'Паказаць карту' in str(page_coordinates_content):
								page_coordinates_content_div = page_coordinates_content.find('span',{"title":"Паказаць карту"})
								print("Паказаць карту")
							
							elif ('id="coordinates' in str(page_coordinates_content)) and (key == 'ptwiki'):
								page_coordinates_content_div = page_coordinates_content.find('div',{"id":"coordinates"})
								print("div coordinates id")
							
							elif ('plainlinksneverexpand' in str(page_coordinates_content)) and (key != 'frwiki' and key != 'myvwiki' and key != 'eowiki' and key != 'hrwiki' and key != 'nnwiki'):
								page_coordinates_content_div = page_coordinates_content.find('div',{"class":"plainlinksneverexpand"})
								print("plainlinksneverexpand")
								
							elif 'coordinatespan' in str(page_coordinates_content):
								page_coordinates_content_div = page_coordinates_content.find('span',{"id":"coordinatespan"})
								print("coordinatespan")
								
							elif 'id="coordinates' in str(page_coordinates_content):
								page_coordinates_content_div = page_coordinates_content.find('span',{"id":"coordinates"})
								print("span coordinates id")
							
							elif 'class="coordinates' in str(page_coordinates_content):
								page_coordinates_content_div = page_coordinates_content.find('span',{"class":"coordinates"})
								print("span coordinates class")


							# if there are some coordinates continue with the scraping
							if (page_coordinates_content_div != '') and (page_coordinates_content_div != None):
								
								# get coordinates from the kartographer
								if 'mw-kartographer-maplink' in str(page_coordinates_content_div):
									page_coordinates_content_a=page_coordinates_content_div.find('a', {"class":"mw-kartographer-maplink"})
									
									print("mw-kartographer-maplink")
									# print(page_coordinates_content_a['data-lat'])
									# print(page_coordinates_content_a['data-lon'])
									
									wiki_geo[key] = str(page_coordinates_content_a['data-lat'])+', '+str(page_coordinates_content_a['data-lon'])
									item[a['title']]['geo_cor']=wiki_geo
									# print(wiki_site)
									
									if item[a['title']]['geo']==False:
										wiki_quick[key] =str(a_data_id)+"|P625|@"+str(page_coordinates_content_a['data-lat'])+"/"+str(page_coordinates_content_a['data-lon'])+"||"
									else:
										wiki_quick[key] = ''
										
									item[a['title']]['wiki_quick']=wiki_quick
									
								else:
									page_coordinates_content_a=page_coordinates_content_div.find('a', {"class":"external text"}, href=True)
									
									if page_coordinates_content_a != None:
										if 'http' in page_coordinates_content_a['href']:
											url_hack=page_coordinates_content_a['href']
										else:
											url_hack='https:'+page_coordinates_content_a['href']
										
										geo_hack = requests.get(url_hack)
										geo_hack_content = BeautifulSoup(geo_hack.content, "html.parser")
								
										# fix for some problems with eswiki
										if key == 'eswiki':
											geo_hack_content=geo_hack_content.find('span',{"class":"geo"})
										
										# get data from cswiki and skwiki
										if key == 'cswiki' or key == 'skwiki':
											n=geo_hack_content
											strange_geo_hack = re.search("\s?(\d+.\d+)°?,\s+(\d+.\d+)°?", str(n))
											geo_hack_latitude=strange_geo_hack.group(1)
											geo_hack_longitude=strange_geo_hack.group(2)
										
										# get data from the rest of the pages
										else:
											geo_hack_latitude=geo_hack_content.find('span',{"class":"latitude"})
											# print(geo_hack_latitude)
											geo_hack_latitude=re.sub('<[^<>]+>', '', str(geo_hack_latitude))
											
											geo_hack_longitude=geo_hack_content.find('span',{"class":"longitude"}) 
											# print(geo_hack_longitude)
											geo_hack_longitude=re.sub('<[^<>]+>', '', str(geo_hack_longitude))
											
											
										if (geo_hack_latitude=='None') and (geo_hack_longitude=='None'):
											wiki_geo[key] = ''
											wiki_quick[key] = ''
										else:
											wiki_geo[key] = geo_hack_latitude+', '+geo_hack_longitude
											
											if item[a['title']]['geo']==False:
												wiki_quick[key] =str(a_data_id)+"|P625|@"+str(geo_hack_latitude)+"/"+str(geo_hack_longitude)+"||"
											else:
												wiki_quick[key] = ''
										
										item[a['title']]['geo_cor']=wiki_geo
										# print(wiki_site)
										
										item[a['title']]['wiki_quick']=wiki_quick
									else:
										wiki_geo[key] = ''
										item[a['title']]['geo_cor']=wiki_geo
										# print(wiki_geo)
										
										wiki_quick[key] = ''
										item[a['title']]['wiki_quick']=wiki_quick

							else:
								wiki_geo[key] = ''
								item[a['title']]['geo_cor']=wiki_geo
								# print(wiki_geo)
								
								wiki_quick[key] = ''
								item[a['title']]['wiki_quick']=wiki_quick

						else:
							pass
							
					# end of the links
					# print("------------------------------------------------------------------------------------------------")
					wiki_site=[]
					wiki_title=[]
					wiki_url=[]
					wiki_geo={}
					wiki_quick={}
				except:
					pass
					
			except:
				pass
				
		# counting the number of elements
		length=len(title_list)

	else:
		return redirect(url_for('index'))
		
	return render_template("wiki_table.html", length=length, title_list=title_list, item=item)
	
if __name__ == '__main__':
	app.run()