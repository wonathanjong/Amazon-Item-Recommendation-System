import os
import pandas as pd
import json
import math
from scipy import spatial
import numpy as np
import pickle
import datetime

data = {}

#using json to store python data structures as files bc it's fast // could use pickle to optijmize for size rather than speed
def save_obj(obj, name):
    with open('obj/'+ name + '.json', 'w') as fp:
        json.dump(obj, fp)

def load_obj(name):
    with open('obj/' + name + '.json', 'r') as fp:
        return json.load(fp)

#use pickle to optimize file size over performance
def save_obj_pickle(obj, name):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj_pickle(name):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

def determineTop10Products():
    productsCount={}
    #load item and customer list
    itemProductsDict = load_obj("uniqueItemsAndCustomers")
    sortedProductList = list(sorted(itemProductsDict.items(), key=lambda x: x[1]['count'], reverse=True))
    top10List = {}
    count = 0
    print("determining top 10 products")
    for product in sortedProductList:
        #check to make sure product is not NaN
        if isinstance(product[0], str) and product[0] != "NaN":
            description = product[0].lstrip()
            description = product[0].rstrip()
            count+=1
            prod = {"Description": description, "stockCode": product[1]['stockCode'], "count": product[1]['count']}
            print(prod)
            top10List[description] = prod
        if count==10:
            break
    save_obj(top10List, "top10List")

#get inventory quantity and date/time data for every top 10 item product
def getPertinentDataByProduct():
    top10List = load_obj("top10List")
    pertinentDataDict = {}
    #load excel file
    xlsx = pd.ExcelFile('Online_retail_Data.xlsx')
    data = pd.read_excel(xlsx, sheet_name='Online Retail')

    #parse through rows of excel
    for index, row in data.iterrows():
        #checks edge case that description is string
        if isinstance(row['Description'], str):
            #strip description of extraneous spacess
            description = row['Description'].lstrip()
            description = description.rstrip()
            #check if description is in top 10 products
            if description in top10List:
                #format invoice date as time
                timey = row['InvoiceDate']
                if description in pertinentDataDict:
                    pertinentDataDict[description][timey.timestamp()] = {"InvoiceDate": timey.strftime("%m/%d/%Y %I:%M %p"), "quantity": row['Quantity'], "year": timey.year, "month":timey.month, "day":timey.day}
                else:
                    pertinentDataDict[description] = {timey.timestamp(): {"InvoiceDate": timey.strftime("%m/%d/%Y %I:%M %p"), "quantity": row['Quantity'], "year": timey.year, "month":timey.month, "day":timey.day}}

    save_obj(pertinentDataDict, "top10PertinentData")

#write pertinent info for top 10 to excel sheet per week
def writeToExcelForSeasonalityAnalysis():
    top10PertinentData = load_obj("top10PertinentData")
    top10AnalysisData = {}

    #sort top 10 items pertinent data by time least to greatest
    for item, itemData in top10PertinentData.items():
        top10AnalysisData[item] = list(sorted(itemData.items()))

    writer = pd.ExcelWriter('Problem3.xlsx')
    #go through each top 10 item
    print(len(top10PertinentData))
    print(len(top10AnalysisData))
    for item, itemData in top10AnalysisData.items():
        count=0
        firstRun = True
        year = 0
        month = 0
        df= pd.DataFrame(columns=['Year', 'Month', 'Quantity'])

        #go through pertinent data
        for dataPoint in itemData:
            if firstRun:
                df.at[count, 'Quantity'] = 0
                year = dataPoint[1]['year']
                month = dataPoint[1]['month']
                df.at[count, 'Year'] = dataPoint[1]['year']
                df.at[count, 'Month'] = dataPoint[1]['month']
                firstRun = False
            elif year != dataPoint[1]['year'] or month != dataPoint[1]['month']:
                count+=1
                df.at[count, 'Quantity'] = 0
                df.at[count, 'Year'] = dataPoint[1]['year']
                df.at[count, 'Month'] = dataPoint[1]['month']

            year = dataPoint[1]['year']
            month = dataPoint[1]['month']

            df.at[count, 'Quantity'] += dataPoint[1]['quantity']

        #write specific item to excel sheet
        df.to_excel(writer, item[:31])

    writer.save()




def main():
    determineTop10Products()
    getPertinentDataByProduct()
    writeToExcelForSeasonalityAnalysis()


if __name__== "__main__":
  main()
