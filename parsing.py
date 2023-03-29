from bs4 import BeautifulSoup
import requests
import re
import json

url = "https://www.tiflofilm-online.ru/"

response = requests.get(url)

#print(response.text)

bs = BeautifulSoup(response.text, 'html.parser')

href_tags = bs.find_all(href=True)

#print(href_tags)

#print(bs)

categories = dict()

for line in bs.find_all('li', re.compile('cat-item cat-item-\d{1,2}')):
    categories.update({line.text: line.a["href"]})

print(categories)
categories.pop("Аудио подкасты\n")

categoryFilms = dict()


for category in categories:
    print(category)
    categoryFilms.update({category.replace('\n', ''): list()})
    caturl = categories[category]
    catresponse = requests.get(caturl)
    catbs = BeautifulSoup(catresponse.text, 'html.parser')
    while(len(catbs.find_all('a', "nextpostslink")) != 0):
        for film in catbs.find_all('h2', "entry-title entry_title"):
            #print(film)
            filmurl = film.a["href"]
            filmres = requests.get(filmurl)
            filmbs = BeautifulSoup(filmres.text, 'html.parser')
            #print(filmbs)

            #print(filmbs.find("h1", "entry-title").text)
            #print(filmbs.find("p").text)

            if len(filmbs.find_all("a", re.compile("button \w{,7} \w{,7}"))) != 0:
                filmdict = {"name": filmbs.find("h1", "entry-title").text, "url": filmbs.find("a", re.compile("button \w{,7} \w{,7}"))['href'], "description": filmbs.find("p").text}
            else:
                print("DROP!!!!!")
                print(filmbs)
                break
            print(filmdict)
            #print(catbs)
            #stop
            categoryFilms[category.replace('\n', '')].append(filmdict)
        caturl = catbs.find('a', "nextpostslink")['href']
        catresponse = requests.get(caturl)
        catbs = BeautifulSoup(catresponse.text, 'html.parser')

for key in categoryFilms:
    print(str(key) + " " + str(categoryFilms[key]))

with open('result.json', 'w') as fp:
    json.dump(categoryFilms, fp,  ensure_ascii=False)
