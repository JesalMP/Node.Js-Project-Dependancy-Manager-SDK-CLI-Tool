import sys
import traceback
import logging
import os
import csv
import urllib
import json
from datetime import datetime
import warnings
import base64
import requests
warnings.simplefilter(action='ignore')
import pandas as pd
from urllib.request import urlopen
from packaging import version
from env import config

def create_data_frame_from_csv(url,truth):
    df= pd.read_csv(url)
    df["version"]=""
    df["version_satisfied"]=False
    if truth:
    	df["update_pr"]=""
    return df
    
    
def create_raw_github_packageVersion_link(url):
    git_repo_url = ""+url+config.packagelink
    git_repo_url=git_repo_url.replace("https://github.com/",config.rawlinkprefix)
    return git_repo_url
    
    
def createGithubPR(token,title,body,head,base,url):

	headers = {
		"Authorization" : "token {} ".format(token),
		"Accept" : "application/vnd.github.v3+json"
	}
	data={
	
        	"title": title,
        	"body": body,
        	"head": head,
        	"base": base,
	}
	url=url.replace("github.com","api.github.com/repos")
	url=url+"/pulls"
	try :
		response = requests.post(url,data=json.dumps(data),headers=headers)
		github201responsjson = response.json()
		return github201responsjson["html_url"]
		
	except:
		#https://api.github.com/repos/OWNER/REPO/pulls
		response = requests.get(url,headers=headers)
		github201responsjson = response.json()
		ll=0
		for i in github201responsjson:
			if i["user"]["login"]==config.user_name:
				ll = i["number"]
				break
		url=url+"/"+str(ll)
		response = requests.patch(url,data=json.dumps(data),headers=headers)
		github201responsjson = response.json()
		return github201responsjson["html_url"]
	#print(response.json())
	
	
	
def getVersionFromRepo(token,url,package):

	headers = {
		"Authorization" : "token {} ".format(token),
		"Accept" : "application/vnd.github.v3+json"
	}
	url=url.replace("github.com","api.github.com/repos")
	url=url+"/contents/package.json"
	response = requests.get(url,headers=headers)
	githubresponsejson = response.json()
	#print(githubresponsejson)
	url=githubresponsejson["content"]
	url=url.replace("\n","")
	url=base64.b64decode(url)
	obj = json.loads(url)
	return obj["dependencies"][package]
	
def getPackageJSONFromRepo(token,url):

	headers = {
		"Authorization" : "token {} ".format(token),
		"Accept" : "application/vnd.github.v3+json"
	}
	url=url.replace("github.com","api.github.com/repos")
	url=url+"/contents/package.json"
	response = requests.get(url,headers=headers)
	githubresponsejson = response.json()
	url=githubresponsejson["content"]
	url=url.replace("\n","")
	url=base64.b64decode(url)
	obj = json.loads(url)
	return obj
	
	
def createGithubRepoFORK(token,url):

	headers = {
		"Authorization" : "token {} ".format(token),
		"Accept" : "application/vnd.github.v3+json"
	}
	url=url.replace("github.com","api.github.com/repos")
	url=url+"/forks"
	response = requests.post(url,headers=headers)
	#print(response.json())
	githubresponsjson = response.json()
	return githubresponsjson["html_url"]
	
	
#      REFERENCE TAKEN FROM https://gist.github.com/ursulacj/36ade01fa6bd5011ea31f3f6b572834e for below functions... Huge +rep to them...	
	
def gh_sesh(user, token):
    s = requests.Session()
    s.auth = (user, token)
    s.headers = {'accept': 'application/vnd.github.v3+json'}
    return s


class GH_Response_Obj:
    def __init__(self, json_all, next_page):
        self.json_all = json_all
        self.next_page = next_page


def gh_get_request(gh_user, gh_token, url):
    s = gh_sesh(gh_user, gh_token)
    response = s.get(url)
    response_status = response.status_code
    if response_status > 200:
        print(f'\n ERROR : This was the response code: {response_status}')
        exit()

    json = response.json()
    links = response.links

    try:
        next_page = links['next']['url']
    except:
        next_page = None

    full = GH_Response_Obj(json, next_page)

    return full


def gh_post_request(gh_user, gh_token, url, data):
    s = gh_sesh(gh_user, gh_token)
    response = s.post(url, data)
    response_status = response.status_code
    if response_status > 201:
        print(f'\n ERROR: This was the response code: {response_status}')
        exit()

    json = response.json()

    return json 


def get_branch_sha(gh_token,gh_user, branch_name,url):
	'''
		Input the FULL repo name in the owner/repo_name format. Ex: magento/knowledge-base
		Defaults to master branch. If you don't want to use the master branch, use a different argument.
	'''

	#url = f'https://api.github.com/repos/""MP/cse3505/branches/main'
	url=url+"/branches/"+branch_name
	response =gh_get_request(gh_user, gh_token, url)
	sha = response.json_all['commit']['sha']
	return sha


def create_new_branch(gh_user, gh_token, master_branch_sha, url,branchname):
	now = str(datetime.now()).replace(' ', '__').replace(':', '-').replace('.', '')
	#new_sync_branch = f'new_branch_{now}'
	
	url=url+"/git/refs"
	#url = "https://api.github.com/repos/""MP/cse3505/git/refs"

	data = {
		"ref": 'refs/heads/'+branchname,
		"sha": master_branch_sha
	}

	data = json.dumps(data)
	
	response =gh_post_request(gh_user, gh_token, url, data)
	
	return response
	
	
def createBranchOfRepoWithVersion(token,url,version):
	headers = {
		"Authorization" : "token {} ".format(token),
		"Accept" : "application/vnd.github.v3+json"
	}
	url=url.replace("github.com","api.github.com/repos")
	
	gh_user = config.user_name
	gh_token = config.token
	sha = get_branch_sha(gh_token,gh_user,"main",url)
	new_sync_branch = create_new_branch(gh_user, gh_token, sha,url,version)
	
	
	
#      HUGE SHOUT OUT TO https://stackoverflow.com/users/14122035/arthur-miranda for explaining in better way then gihub for commit  APIs. https://stackoverflow.com/questions/#11801983/how-to-create-a-commit-and-push-into-repo-with-github-api-v3

def UpdateJsonOnRepo(token,url,filename,updatedjson):
	
	headers = {
		"Authorization" : "token {} ".format(token),
		"Accept" : "application/vnd.github.v3+json"
	}
	#url="https://api.github.com/repos/""MP/cse3505/commits/main"
	urlMain=url.replace("github.com","api.github.com/repos")
	url=urlMain+"/commits/main"
	response = requests.get(url,headers=headers)
	jsoon=response.json()
	last_commit_sha = jsoon['sha']
	sample_string_bytes = updatedjson.encode("ascii")
	base64_bytes = base64.b64encode(sample_string_bytes)
	base64_string = base64_bytes.decode("ascii")
	data={
  	"content":base64_string,
	"encoding": "base64"
	}
	url=urlMain + "/git/blobs"
	response = requests.post(url,data=json.dumps(data),headers=headers)
	jsoon1=response.json()
	base64_blob_sha = jsoon1["sha"]
	data=  {
   	"base_tree": last_commit_sha,
   	"tree": [
     	{
     	"path": filename,
     	"mode": "100644",
	"type": "blob",
	"sha": base64_blob_sha
	}
	]
	}
	#url="https://api.github.com/repos/""MP/cse3505/git/trees"
	url=urlMain+"/git/trees"
	response = requests.post(url,data=json.dumps(data),headers=headers)
	jsoon1=response.json()
	tree_sha = response.json()['sha']
	# POST /repos/:owner/:repo/git/commits
	data =  {
	"message": "Updating Version of Dependancies in "+ filename,
	"author": {
	"name": config.user_name,
	"email": config.user_mailid
	},
	"parents": [
	last_commit_sha
	],
	"tree": tree_sha
	}

	url=urlMain + "/git/commits"
	response = requests.post(url,data=json.dumps(data),headers=headers)

	new_commit_sha = response.json()['sha']
	data =  {
	"ref": "refs/heads/master",
	"sha": new_commit_sha
	}
	url=urlMain+"/git/refs/heads/main"
	response = requests.post(url,data=json.dumps(data),headers=headers)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	


	
	
	
	
	
	
	
	
	
	
	
