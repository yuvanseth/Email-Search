from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
#from Email-Search.e-mail import uids
from conf import *
import requests
import json
import os
import sys
sys.path.insert(0,'/Users/raghuramg/wsfun/raghuallinonevenv/lib/python3.7/site-packages/eml2pdflib')
import eml2pdflib
from eml2pdflib.lib.eml2html import EmailtoHtml
from eml2pdflib.lib.html2img import HtmltoImage
app = Flask(__name__)

html_to_image_convertor = HtmltoImage()
import pdb
@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    #Make a call to elastic search. Get most recent emails and 
    #convert to them to images. Show those images here.

    path = ELASTICSEARCHSERVERADDRESS + "/" + ELASTICSEARCHINDEX + "/_search/"
    queryParams = dict()
    queryParams['query'] = { "match_all": {} };
    payloadForElasticSearchAsJsonStr = json.dumps(queryParams)
    #queryParams['sort'] = { "account_number": "asc" }
    response = requests.get(path)
    response = requests.get(path, data=payloadForElasticSearchAsJsonStr, headers={"Content-Type":"application/json", "Accept":"*/*", "User-Agent":"curl/7.64.1"})
    if (response.status_code < 200 or response.status_code >= 300):
        logging.error("Getting document from elastic search failed response status=%s reason=%s",
               response.status_code, response.reason)
    responseAsDict = json.loads(response.content)
    hitsLevel1 = responseAsDict.get('hits',None)
    if (hitsLevel1 == None):
        #TODO: Ideally need to give no results response.
        render_template('index.html')
    hitsLevel2 = hitsLevel1.get('hits',None)
    if (hitsLevel2 == None):
        #TODO: Ideally need to give no results response.
        render_template('index.html')
    MAXRESULTS = 3
    output_dir = "Images/"
    count = 0
    imageList = []
    for hit in hitsLevel2:
        try:
            #the body here is basicaly html code.
            html =  hit['_source']['body']
            filename = str(count) + ".jpg"
            img_path = html_to_image_convertor.save_img(
                html.encode(), output_dir, filename)
            imageList.append(filename)
            count= count +1 
            if (count == MAXRESULTS):
                break
        except Exception as e: 
            print(e)

    pdb.set_trace()
    render_template('index.html', imageList=imageList)

@app.route("/about")
def about():
    render_template('about.html')

@app.route("/signup")
def signup():
    render_template('signup.html')

@app.route("/blog")
def blog():
    render_template('#blog')


if __name__ == "__main__":
    app.run()
