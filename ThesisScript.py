#!/usr/bin/env python
# coding: utf-8

# RUN THIS FILE WITH:
#    python -i ThesisScript.py 

# Load libraries and settings
import matplotlib
#get_ipython().run_line_magic('matplotlib', 'inline') # Used for jupyter
import os
import time
import datetime
import json
from datetime import datetime
from time import gmtime, strftime
from random import randint
import re
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'font.size': 12})
import pandas as pd
from psaw import PushshiftAPI
import csv
import sys
import warnings
warnings.filterwarnings("ignore")
#pd.set_option('display.max_colwidth', -1) # We want all comment text visible in notebook



# Convert from epoch to Y-M-D
def timeInvert(epoch):
    return time.strftime('%Y-%m-%d', time.localtime(epoch))
# Convert to epoch from Y-M-D
def timeConvert(date):
    utc_time = datetime.strptime(date, "%Y-%m-%d")
    epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
    return int(epoch_time)

# Fetch method using psaw. Fetches comments + metadata containing searchwword from subreddit between _after and _before
def fetch(_searchword, _subreddit, _after, _before):
    api =  PushshiftAPI()
    gen =  api.search_comments(q=_searchword, 
                               subreddit=_subreddit,
                               #limit=100,
                               after=_after,
                               before=_before
                               #,filter=['body','created_utc']
                               )
    return list(gen)

# Create date tuples. Since we are dealing with monthly timeseries data, we need tuples containing from-date and to-date:
def createDateTuples():
    years = ["2020", "2021"]
    startList = []
    dateTuples = []
    for year in years:
        for i in ["%.2d" % i for i in range(1,13)]:
            startList.append(year + "-" + i + "-01")        

    for idx, date in enumerate(startList[:-1]):
        #dateTuples.append((date, startList[idx+1]))
        dateTuples.append((timeConvert(date), timeConvert(startList[idx+1])))

    return dateTuples[:13] # Limit dates from JAN1 2020 to FEB1 2020


# The crawler:
# Crawls subreddit for each searchword in list between dates and saves to dataframe ('df')
# Dataframe then pickled to 'data/df' for later use
# The crawler finished in 36693sec / ~10 hours
def crawler(_dateTuples, _searchwords, _subreddits, _isTest):
    if os.path.isfile('data/df'):
        continueCrawl = input("df file already exists. Are you sure you want to execute crawler again and overwrite existing df file? Y/N\n")
        if continueCrawl.lower() == "y" or continueCrawl.lower() == "yes":
            print("Continuing")
        else:
            print("Crawler cancelled")
            return
    df = pd.DataFrame()
    includedColumns = ["author", "body", "created_utc", "id", "searchword"]
    start = time.time()
    if _isTest:
            _dateTuples = _dateTuples[:1]
            _searchwords = _searchwords[:1]

    for searchword in _searchwords:
        for subreddit in _subreddits:
            for period in _dateTuples:
                print("Seachword: " + searchword)
                print("Between dates: " + timeInvert(period[0]) + " and " + str(timeInvert(period[1])))
                filename = "data/" + timeInvert(period[0]) + ".txt"
                comments = fetch(searchword, subreddit, period[0], period[1])
                print("Found " + str(len(comments)) + " comments \n")
                tempdf = pd.DataFrame([comment.d_ for comment in comments])
                tempdf['searchword'] = pd.Series(searchword, index=tempdf.index)
                if df.empty:
                    df = tempdf
                else:
                    df = pd.concat([df,tempdf], axis=0).reset_index(drop=True)
                    #df = df.loc[df.astype(str).drop_duplicates().index]
                    df = df.groupby(includedColumns[:-1])['searchword'].apply(lambda x: ','.join(x)).reset_index()
                    df.to_pickle("data/df")

    end = time.time()
    print("Finished in: " + str(end - start))
    return df

# If crawler has already executed, and a local df is available, use load:
def loadExistingDf():
    return pd.read_pickle("data/df")

# Initial Comment Cleaning. Removes quotes, urls/reddit links
def initialCommentClean(_comment, _pattern):
    s = "\n".join([e if '&g' not in e else "" for e in _comment.splitlines()]) # Remove quotes
    s = _pattern.sub(r'\1', s) # Remove links with hyperlink text, return the text instead
    s = "\n".join([e if 'http' not in e and '/r/' not in e else "" for e in s.splitlines()]) # Remove normal and reddit links
    #s = s.replace("\n", " ")
    s = " ".join(s.splitlines())
    return s

# Updates rows after cleaning (searchword from 'searchwords' column, if no keywords are present in 'body')
def updateRow(_df):
    return ",".join([e for e in _df["searchword"].split(',') if e in _df["body"].lower()])

# Applies cleaning to given df
def applyCleaning(_df):
    pattern = re.compile('\[(.*?)\]\(.*?\)') # regex pattern for removing links
    #newDf = _df.copy() # Create copy of original df
    newDf = _df.copy()

    newDf = newDf[newDf['author'].apply(lambda x: x != "AutoModerator")] # Remove automoderator posts
    newDf['id2'] = newDf.groupby(['author']).ngroup() # Create unique id instead of authorname
    newDf['body'] = newDf['body'].map(lambda x: initialCommentClean(x, pattern)) # Apply initialclean method to comments
    newDf['searchword'] = newDf.apply(updateRow, axis=1) # Remove searchword from 'searchwords' if removed from 'body'
    newDf = newDf[newDf['searchword'].apply(lambda x: len(x) > 0)] # Remove rows where all 'searchwords' has been removed
    newDf = newDf.drop("author", 1) # Drop author column
    return newDf

# Export comments to .txt file:
def exportCommentsToTxt(_newDf):
    with open('newfile.txt', 'w', encoding='utf-8') as f:
        for text in newDf['body'].tolist():
            f.write(text + '\n')

# Create local keyness analysis with scores, saves results to data/warSWs_KeynessScores.csv
def keynessAnalysis():
    warterms = pd.read_csv("data/warterms.csv", 
                      sep=';', 
                      names=["Word", "fwpm", "rwpm"])

    N = 1 # 
    warterms["KeynessScore"] = (warterms['fwpm']+N) / (warterms['rwpm']+N)
    warterms.to_csv("data/warSWs_KeynessScores.csv", sep=';')
    return warterms

# Calculate number of comments collected in each month for each searchword
# Create df to store this information in
# Create plot
# Save to csv for excel
def frequencyAnalysis(_newDf, _dateTuples):
    numberOfComments = []

    for tup in _dateTuples:
        numberOfComments.append(len(_newDf.loc[(_newDf['created_utc'] >= tup[0]) & (_newDf['created_utc'] <= tup[1])]))   
                  
    commentFrequency = {}        
    for searchword in searchwords:
        monthly = []
        for tup in _dateTuples:
            monthly.append(len(_newDf.loc[(_newDf['created_utc'] >= tup[0]) & (_newDf['created_utc'] <= tup[1]) & (_newDf['searchword'].str.contains(searchword))]))
        commentFrequency[searchword] = monthly

    times = [timeInvert(e[0]) for e in _dateTuples]
    import seaborn as sns
    sns.set(color_codes=True)
    fig=plt.figure(figsize=(20, 12), dpi= 80, facecolor='w', edgecolor='k')

    x = [e for e in range(len(_dateTuples))]
    plt.xticks(x, times)

    plt.xticks(fontsize=14, rotation=90)
    plt.yticks(fontsize=14)
    plt.ylabel('Number of comments')
    plt.xlabel('Month')
    for searchword in searchwords:
        plt.plot(commentFrequency[searchword],label=searchword, linestyle='-', marker='o')
    plt.legend()
    plt.savefig("data/SearchwordFrequencyMonth.png")


    with open('monthlycomments.csv','w') as file:
        for row in commentFrequency:
            file.write(row+";"+";".join(str(commentFrequency[row])))
            file.write('\n')



    commentFrequencyDf = pd.DataFrame(commentFrequency)
    commentFrequencyDf.to_csv("data/monthlyComments.csv", sep=';')
    return commentFrequencyDf


subreddits = ["coronavirus"]
searchwords = ["covid", "corona", "sars-cov-2", "2019-ncov", "pandemic", "epidemic", "outbreak", "pneumonia", "illness", "disease", "sickness", "virus", "germ", "bacteria", "influenza", "symptom", "infect", "transmit"]
dateTuples = createDateTuples()

print("\n")
print("\n")
print("\n")
print("\n")
print("- Crawler - To run test crawler do:")
print("\t'df = crawler(dateTuples, searchwords, subreddits, True)'\n")

print("- Crawler - To run full crawler do:")
print("\t'df = crawler(dateTuples, searchwords, subreddits, False)'. Warning: Takes ~10 hours to finish\n")

print("- Load data - If crawler has executed, or df file exists, just load raw psaw data from file:")
print("\t'df = loadExistingDf()'\n")

print("- Clean data - Clean the loaded dataframe with:")
print("\t'newDf = applyCleaning(df)'\n")

print("- Export data - Export the cleaned data to txt file for sketchengine:")
print("\t'exportCommentsToTxt(newDf)'\n")

print("- Keyness analysis: Calculate keyness scores using existing file with frequency per million and save to csv. Do:")
print("\t'keynessAnalysis()'\n")

print("- Frequency analysis. Frequency of each searchword each month. Save plot and data to file. Do:")
print("\t'frequencyAnalysis(newDf, dateTuples)'\n")