import sys
import traceback
import logging
import os
import csv
import shutil
from tabulate import tabulate
import urllib
import json
import warnings
import subprocess
from halo import Halo
warnings.simplefilter(action='ignore')
import pandas as pd
import argparse
from pyfiglet import Figlet
import pyfiglet as pyg  
from urllib.request import urlopen
from packaging import version
from env import config
from env.config import token
from utils import functions



logging_format = '[%(asctime)s||%(name)s||%(levelname)s]::%(message)s'
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"),
                    format=logging_format,
                    datefmt='%Y-%m-%d %H:%M:%S',)
logger = logging.getLogger(__file__)



def main():

    PRcheck=False
    res1= pyg.figlet_format("Dependancy Manager CLI tool in python")
    res2= pyg.figlet_format("B Y")
    res3= pyg.figlet_format("1 9 B C E 1 2 5 9")
    print(res1)
    print(res2)
    print(res3)
    parser = argparse.ArgumentParser(description='Dyte CLI python management tool to update dependancies of Node.js packages/projects via CLI, By Patel Jesal Manoj, 19BCE1259')
    parser.add_argument("-version","-v", help="Sets the Target version of dependancy", required=True,metavar="version")
    parser.add_argument("-dependancy","-d", help="Sets the Required dependancy name", required=True,metavar="dependancy")
    parser.add_argument("-input","-i", help="Set the location of target input csv file containing Repos and their current version", required=True,metavar="input")
    parser.add_argument("-update","-u", help="Use this if you want to fork the project repo and change/update the dependancies in package.json and packages-lock.json, and then create a pull request to main repo to merger updated dependancies of package.json and packages-lock.json.", action='store_true')
    
    
    args = parser.parse_args()
    spinner = Halo(text='Loading', spinner='dots')
    spinner.start()
    
    version_set = args.version
    dependancy_set = args.dependancy
    fileLink=""+args.input
    if args.update:
    	PRcheck=True
    #if args.setauthkey:
    	#token=args.setauthkey
    #logger.info(PRcheck)
    
    
    df=functions.create_data_frame_from_csv(fileLink,PRcheck)
    spinner.succeed("Dataframe for Processing Created.")
    spinner.start()
    for ind in df.index:
    	pd.options.mode.chained_assignment = None
    	#git_repo_url = functions.create_raw_github_packageVersion_link(df["repo"][ind])
    	git_repo_url = df["repo"][ind]
    	
    	#rr= functions.getPackageJSONFromRepo(config.token,git_repo_url)
    	#print(rr)
    	repo_current_version = functions.getVersionFromRepo(config.token,git_repo_url,dependancy_set)
    	spinner.succeed("Version extracted from Provided repo " + df["name"][ind])
    	spinner.start()
    	repo_current_version=repo_current_version.replace("^","")
    	repo_current_version=repo_current_version.replace("~","")
    	
    	version_satisfied=version.parse(version_set)<=version.parse(repo_current_version)
    	
    	if version_satisfied==False and PRcheck == True:
    		forkedUrl=functions.createGithubRepoFORK(config.token,git_repo_url)
    		spinner.succeed("Fork for repo " + df["name"][ind]+ " Created")
    		spinner.start()
    		packagejson=functions.getPackageJSONFromRepo(config.token,forkedUrl)
    		currDir=os.getcwd()
    		shutil.rmtree("temp")
    		os.mkdir("temp")
    		os.chdir("temp")
    		os.mkdir(df["name"][ind])
    		os.chdir(df["name"][ind])
    		packagejson["dependencies"][dependancy_set]=version_set
    		
    		spinner.succeed("package.json of " + df["name"][ind]+ " Extracted")
    		spinner.info("Creating package-lock.json for "+ df["name"][ind]+", IT MAY TAKE SOME TIME, so hold on.")
    		spinner.start()
    		with open('package.json', 'w') as outfile:
    			json.dump(packagejson, outfile)
    		subprocess.check_call('npm i --package-lock-only --silent', shell=True,stderr=subprocess.DEVNULL)
    		
    		spinner.succeed("package-lock.json for repo " + df["name"][ind]+ " Created")
    		spinner.start()
    		with open('package.json') as f:
    			packagedotjson = json.load(f)
    		packagedotjsonStringTemp=json.dumps(packagedotjson,indent=2)
    		functions.UpdateJsonOnRepo(config.token,forkedUrl,"package.json",packagedotjsonStringTemp)
    		
    		with open('package-lock.json') as f:
    			packagelockdotjson = json.load(f)
    		packagelockdotjsonStringTemp=json.dumps(packagelockdotjson,indent=2)
    		functions.UpdateJsonOnRepo(config.token,forkedUrl,"package-lock.json",packagelockdotjsonStringTemp)
    		spinner.succeed("Commited updated dependancy package.json and package-lock.json to forked repo " + df["name"][ind]+ " With URL "+forkedUrl)
    		spinner.start()
    		os.chdir("..")
    		shutil.rmtree(df["name"][ind])
    		#Updates the version of axios from 0.21.1 to 0.23.0
    		os.chdir(currDir)
    		spinner.info("Creating Pull request for the forked repo to main repo, IT MAY TAKE SOME TIME, so hold on.")
    		spinner.start()
    		PRurl = functions.createGithubPR(config.token,"Chore : Update "+dependancy_set+" to "+version_set,"Updates the version of axios from " + repo_current_version+ " to "+version_set ,config.user_name+":main","main",git_repo_url)
    		df["update_pr"][ind]=PRurl
    		spinner.succeed("DONE for "+df["name"][ind])
    		spinner.start()
    	
    	df["version"][ind]=repo_current_version
    	df["version_satisfied"][ind]=version_satisfied
    	spinner.start()
    	
    
    spinner.info("The CSV output has been saved to output.csv in root directory.")	
    df.to_csv('output.csv')
    #print(df.to_markdown())
    print(tabulate(df, headers='keys', tablefmt='grid'))
    spinner.stop()
    	
    


if __name__ == '__main__':
    main()
