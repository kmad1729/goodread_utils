import requests
import xml.etree.ElementTree as ET
from requests_oauthlib import OAuth1Session, OAuth1
from keys import key, secret

main_url = "http://www.goodreads.com"

request_token_url =    main_url + '/oauth/request_token'
auth_url =             main_url + "/oauth/authorize/"
access_token_url =     main_url + "/oauth/access_token"
user_id_url =          main_url + '/api/auth_user'
user_owned_books_url = main_url + '/owned_books/user?format=xml'
mem_shelf_url =        main_url + '/review/list?format=xml&v=2'

class Book(object):
    def __init__(self, bookElemTreeObject):
        ''' creating a book object from elemtree book object '''
        for child in bookElemTreeObject:
            tag_name = child.tag
            if child.text:
                setattr(self, tag_name, child.text)

    def __repr__(self):
        return self.title

###### OAUTH1 REQUEST PHASE ######

oauth1_request_phase = OAuth1Session(key, client_secret=secret)

r = oauth1_request_phase.fetch_request_token(request_token_url)
k1 = r.get('oauth_token')
s1 = r.get('oauth_token_secret')


user_authentication_url = (oauth1_request_phase.authorization_url(auth_url))

auth_resp = raw_input("paste the following link in your browser: \n\n %s \n\n "
                "and paste the response: " % user_authentication_url)

oauth_resp = oauth1_request_phase.parse_authorization_response(auth_resp)

###### OAUTH1 ACCESS PHASE ######

access_tok = oauth_resp.get('oauth_token')

oauth1_access_phase = OAuth1Session(key, client_secret=secret, 
                resource_owner_key=k1, resource_owner_secret=s1, verifier="foo")

resource_owner_resp = oauth1_access_phase.fetch_access_token(access_token_url)

resource_owner_key = resource_owner_resp.get('oauth_token')
resource_owner_secret = resource_owner_resp.get('oauth_token_secret')

#### FINAL USABLE OAUTH1SESSION ####
session_object = OAuth1Session(key, client_secret=secret, 
                resource_owner_key=resource_owner_key, 
                resource_owner_secret=resource_owner_secret)

def get_verifier_user_id(session_object):
    resp = session_object.get(user_id_url)
    if resp.status_code != 200:
        raise requests.HTTPError(resp.content)
    data = ET.fromstring(resp.content)
    return data.find('user').attrib['id']
    

userId = get_verifier_user_id(session_object)

def get_user_owned_books(session_object, userId):
    params = {"id" : userId}
    resp = session_object.get(user_owned_books_url, params = params)

    if resp.status_code != 200:
        raise requests.HTTPError(resp.content)

    data = ET.fromstring(resp.content)
    return [Book(b) for b in data.findall('owned_books/owned_book/book')]

def get_books_from_user_shelf(session_object, userId, shelf_name = "read", 
                                sort_by = "date_read", per_page = None):
    
    #roundabout way to get the developer key
    key = session_object._client.client.client_key

    mem_shelf_params = {
        "id": userId,
        "shelf": shelf_name,
        "sort": sort_by,
        "key":key,
    }

    if per_page:
        mem_shelf_url["per_page"] = per_page

    resp = session_object.get(mem_shelf_url, params = mem_shelf_params)

    data = ET.fromstring(resp.content)

    with open('books.xml','w') as f:
        f.write(resp.content)

    return [Book(b) for b in data.findall('reviews/review/book')]
    

# Testing the methods
out1 = get_books_from_user_shelf(session_object, userId)
out2 = get_user_owned_books(session_object, userId)


