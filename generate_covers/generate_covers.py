import re
from joblib import Parallel, delayed
import multiprocessing
import urllib.request
from urllib.error import HTTPError
import time


FILE_NAME = "machule.txt"
OUT_FILE_NAME = "covers.css"
ANIME_HREF_PATTERN = 'href="/anime/([^\/]*)/'
IMAGE_PATTERN = "https://myanimelist.cdn-dena.com/images/anime/.*.jpg"
URL_ANIME = 'https://myanimelist.net/anime/'

def processInput(anime_ref):
	try:
		fp = urllib.request.urlopen(URL_ANIME+anime_ref)
		mybytes = fp.read()
		fp.close()
		mystr = mybytes.decode("utf8")
		return (anime_ref,re.findall(IMAGE_PATTERN,mystr)[1])
	except HTTPError:
		time.sleep(1);
		return processInput(anime_ref)
	

if __name__ == '__main__':
	with open(FILE_NAME,'r') as f:
		raw = f.read()
	refs = re.findall(ANIME_HREF_PATTERN,raw)
	num_cores = multiprocessing.cpu_count()
	results = Parallel(n_jobs=num_cores)(delayed(processInput)(i) for i in refs)
	
	with open(OUT_FILE_NAME,'w+') as f:
		for (ref,url) in results:
			f.write("#more"+str(ref)+"{background-image: url(\""+url+"\");}\n")