from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
#from Email-Search.e-mail import uids
from conf import *
import requests
import json
import os
import sys
sys.path.insert(0,'/Users/yuvanseth/Documents/VS/Email-Search/eml2pdflib')
print(sys.path)
import eml2pdflib
from eml2pdflib.lib.eml2html import EmailtoHtml
from eml2pdflib.lib.html2img import HtmltoImage
import os.path

#app = Flask(__name__)
app = Flask(__name__, static_url_path='')

html_to_image_convertor = HtmltoImage()
import pdb


from flask import Flask, request, send_from_directory

@app.route('/Images/<path:path>')
def send_images(path):
    return send_from_directory('Images', path)


@app.route('/static/<path:path>')
def send_staticfiles(path):
    return send_from_directory('static', path)





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
    queryParams['query'] = { "match": {} }
    payloadForElasticSearchAsJsonStr = json.dumps(queryParams)
    #queryParams['sort'] = { "account_number": "asc" }
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
            fullpath = output_dir+filename
            #Convert only if file does not exist
            if (not os.path.exists(fullpath)):
                pdf_path = html_to_image_convertor.save_img(
                    html.encode(), output_dir, filename)
            imageList.append(filename)
            count= count +1 
            if (count == MAXRESULTS):
                break
        except Exception as e: 
            print(e)

    return render_template('index.html', imageList=imageList)

@app.route("/about")
def about():
    render_template('about.html')

#@app.route("/blog")
#def blog():
    #render_template('blog.html')

@app.route("/signup")
def signup():
    render_template('signup.html')

@app.route("/search", methods=['POST'])
def search():
    path = ELASTICSEARCHSERVERADDRESS + "/" + ELASTICSEARCHINDEX + "/_search/"
    queryParams = dict()
    query = request.form['search']
    queryParams['query'] = { "match_all": { "From": "%s" } } %(query)
    payloadForElasticSearchAsJsonStr = json.dumps(queryParams)
    #queryParams['sort'] = { "account_number": "asc" }
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
            fullpath = output_dir+filename
            #Convert only if file does not exist
            if (not os.path.exists(fullpath)):
                pdf_path = html_to_image_convertor.save_img(
                    html.encode(), output_dir, filename)
            imageList.append(filename)
            count= count +1 
            if (count == MAXRESULTS):
                break
        except Exception as e: 
            print(e)

    return render_template('search.html', imageList=imageList)
