import imaplib
import email
import os
import sys
sys.path.insert(0,'/Users/yuvanseth/Documents/VS/Email-Search/eml2pdflib')
print(sys.path)
import eml2pdflib
from eml2pdflib.lib.eml2html import EmailtoHtml
from eml2pdflib.lib.html2img import HtmltoImage
import json
import requests
import logging
import http.client
from conf import *

EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
EMAIL_PSWD = os.environ['EMAIL_PSWD']
EMAIL_MAILBOX = os.environ['EMAIL_MAILBOX']
IMAP_SERVER = os.environ['IMAP_SERVER']

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

httpclient_logger = logging.getLogger("http.client")
def httpclient_logging_patch(level=logging.DEBUG):
    """Enable HTTPConnection debug logging to the logging framework"""

    def httpclient_log(*args):
        httpclient_logger.log(level, " ".join(args))

    # mask the print() built-in in the http.client module to use
    # logging instead
    http.client.print = httpclient_log
    # to enable debugging change to 1
    http.client.HTTPConnection.debuglevel = 0






class EmailHelper(object):
    def __init__(self, IMAP_SERVER, EMAIL_ADDRESS,
                 EMAIL_PSWD, EMAIL_MAILBOX):
        # logs in to the desired account and navigates to the inbox
        self.mail = imaplib.IMAP4_SSL(IMAP_SERVER, '993')
        self.mail.login(EMAIL_ADDRESS, EMAIL_PSWD)
        self.mail.select()

    def get_emails(self, mail):
        
        x = self.mail.uid('SEARCH', None, '(FROM "{}")'.format(mail))
        uids = x[1][0].split()
        return uids

    def get_email_message(self, email_id):
        email_id = email_id.decode('utf-8')
        _, data = self.mail.uid('FETCH', email_id, '(RFC822)')
        raw_email = data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)
        return email_message


############ MAIN PROGRAM ##############
mails = ['newsletter@e.gizmodo.com', 'marketing@gridgain.com', 'greatschools-newsletters@email.greatschools.org', 'mwwotd@wotd.m-w.com']

email_helper = EmailHelper(IMAP_SERVER, EMAIL_ADDRESS,
                           EMAIL_PSWD, EMAIL_MAILBOX)
email_to_html_convertor = EmailtoHtml()
html_to_image_convertor = HtmltoImage()

httpclient_logging_patch()

dir_path = os.path.dirname(os.path.realpath(__file__))
output_dir = os.path.join(dir_path, "images")

def getMsgIdFromHeaders(headers):
    for headerAndValue in headers:
        #Each headerAndValue is a pair of header name and actual value
        if (headerAndValue[0] == 'Message-ID'):
            return headerAndValue[1]
    return None

count = 0;
MAX_COUNT = 10
for mail in mails[:1]:
    uids = email_helper.get_emails(mail)

    for uid in uids[:3]:
        count = count + 1
        uidAsInt = int.from_bytes(uid,"big")
        logging.info("Attempting fetching of message with uid=%d", uidAsInt)
        try:
            email_message = email_helper.get_email_message(uid)
            payload = email_message.get_payload()
            #make json info out of these messages.
            payloadForElasticSearchIngestion =  email_message.__dict__.copy()
            payloadForElasticSearchIngestion.pop('policy', None) #Apparently Compact32 is not json serializable.
            payloadForElasticSearchIngestion.pop('_payload', None) #We will re-add it at the bottom with key body.
            #payloadForElasticSearchIngestion.pop('_headers', None)
            #payloadForElasticSearchIngestion.pop('_unixfrom', None)
            #payloadForElasticSearchIngestion.pop('_charset', None)
            #payloadForElasticSearchIngestion.pop('preamble', None)
            #payloadForElasticSearchIngestion.pop('epilogue', None)
            #payloadForElasticSearchIngestion.pop('defects', None)
            #payloadForElasticSearchIngestion.pop('_default_type',None)
            #Note that payload could be a list
            payloadAsStr = ""
            if isinstance(payload, list):
                for m in payload:
                    payloadAsStr = payloadAsStr + str(m)
            else:
                payloadAsStr = str(m)
            payloadForElasticSearchIngestion['body'] = payloadAsStr
            
            headers = payloadForElasticSearchIngestion['_headers']
            msgId = getMsgIdFromHeaders(headers)
            
            #Write to a file for debugging purposes.
            filename = "result_" + str(uidAsInt) + ".json"
            with open(filename, 'w') as fp:
                json.dump(payloadForElasticSearchIngestion, fp)
            logging.info("Attempting ingestion of message with uid=%d, msgId=%s", uidAsInt, msgId)
            
            #Just use uid as our primary key. Makes things simple for now.
            path = ELASTICSEARCHSERVERADDRESS + "/" + ELASTICSEARCHINDEX + "/_doc/" + str(uidAsInt)
            payloadForElasticSearchIngestionAsJsonStr = json.dumps(payloadForElasticSearchIngestion)
            logging.info("Posting data to path %s", path)
            response = requests.put(path, data= payloadForElasticSearchIngestionAsJsonStr, headers={"Content-Type":"application/json", "Accept":"*/*", "User-Agent":"curl/7.64.1"})
            #response = requests.put(path, data= payloadForElasticSearchIngestionAsJsonStr)
            if (response.status_code < 200 or response.status_code >= 300):
                logging.error("Adding document to elastic search failed for message with uid=%d msgId=%s response status=%s reason=%s",uidAsInt, 
                                             msgId, response.status_code, response.reason)
                continue
            logging.info("Successfully ingested message with uid=%d ", uidAsInt);
            #All good. Move to next one.   
            if (count > MAX_COUNT):
                logging.info("Max Messages %d ingested in one run has been reached. Not ingesting any more", MAX_COUNT)
                break
            
            #TODO: Store to elastic search instance
            #html = email_to_html_convertor.convert(email_message)
            #filename = str(uid) + ".jpg"
            #pdf_path = html_to_image_convertor.save_img(
            #    html.encode(), output_dir, filename)
            #print(pdf_path)
        except Exception as e: 
            print(e)

    logging.info("Ingested a total of %d messages", count)
    logging.info("Exiting")