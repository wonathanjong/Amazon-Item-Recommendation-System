import os
import pandas as pd
import json
import math
from scipy import spatial
import numpy as np
import pickle

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

def getProductsBoughtTogether(productName):
    product = load_obj("itemCosineSimilarityBasketDictionary")
    product = product[productName]
    sortedProductList = [(k, product[k]) for k in sorted(product, key=product.get, reverse=True)]
    count = 1
    for index, value in enumerate(sortedProductList):
        print("The number " + str(count) + " most similar product to " + productName + " is ")
        print(value)
        print("\n")
        count+=1
        if count ==15:
            return

#calculate jaccard index for the item pairs //very intensive near O(n^3)
def calculateItemSimilarityUsingJaccardIndex():
    itemSimilarity = {}
    itemBasketDictionary = load_obj("itemBasketDictionary")

    #calculate similarity of items by finding union similarity of items purchased divided by total other items purchased
    totalDict = {}
    commonKeys = {}
    #calculate total items purchased with for every item
    for itemOneName, itemOne in itemBasketDictionary.items():
        itemOneTotalItemsPurchasedWith = 0
        for itemTwoName, itemTwo in itemOne.items():
            itemOneTotalItemsPurchasedWith += itemTwo
            itemOneSet = set(itemOne)
            itemTwoSet = set(itemBasketDictionary[itemTwoName])
            commonKeys[itemOneSet] = {itemTwoSet: itemOneSet.intersection(itemTwoSet)}
        totalDict[itemOneName] = itemOneTotalItemsPurchasedWith
    print("done with finding totals")
    save_obj(totalDict, "totalsDictionary")

    print("let's ride")
    #go through all items named item one in item basket
    for itemOneName, itemOne in itemBasketDictionary.items():
        if itemOneName not in itemSimilarity:
            itemSimilarity[itemOneName] = {}
        #go through all items named item two bought with item one
        for itemTwoName, itemTwo in itemOne.items():
            similar = 0
            total = 0
            if itemTwoName not in itemSimilarity[itemOneName]:
                #find common keys between first item group and second item group
                itemOneSet = set(itemOne)
                itemTwoSet = set(itemBasketDictionary[itemTwoName])
                for commonKey in itemOneSet.intersection(itemTwoSet):
                    #add similar counts
                    similar += min(itemOne[commonKey], itemBasketDictionary[itemTwoName][commonKey])*2
                #add totals
                total = totalDict[itemOneName] + totalDict[itemTwoName]
                #calculate jaccard index
                itemSimilarity[itemOneName][itemTwoName] = similar/(total-similar)
                if itemTwoName in itemSimilarity:
                    itemSimilarity[itemTwoName][itemOneName] = similar/(total-similar)
                else:
                    itemSimilarity[itemTwoName] = {itemOneName: similar/(total-similar)}

    save_obj(itemSimilarity, "itemSimilarityDict")

#calculate cosine similarities between vectors of unique items with n dimensions of unique customers purchased
def calculateItemSimilarityUsingCosineSimilarity():
    print("creating similarity basket by item cosine similarity")
    itemCosineSimilarityBasketDictionary = {}
    #load necessary objects
    itemsAndUsersWhoPurchased = load_obj("uniqueItemsAndCustomers")
    userAndItemsPurchased = load_obj("userItemsPurchased")

    #create list of items to parse through as well as a dictionary to identify index of matrix by the item name key
    listOfItems = []
    itemIndexDictionary = {}
    count = 0
    for key, value in itemsAndUsersWhoPurchased.items():
        listOfItems.append(key)
        itemIndexDictionary[key] = count
        count+=1
    #create empty matrix of width and height: length of unique items
    itemBoughtWithOtherItemMatrix = np.zeros((count, count))

    #parse through all unique items boughts
    for indexOne, itemOneName in enumerate(listOfItems):
        #parse through all customers who bought the unique item
        for customer in itemsAndUsersWhoPurchased[itemOneName]['customers']:
            #parse through all of the other items purchased by the selected customer
            for itemTwoName, itemTwo in userAndItemsPurchased[str(customer)].items():
                indexTwo = itemIndexDictionary[itemTwoName]
                if itemTwoName != itemOneName and itemBoughtWithOtherItemMatrix[indexOne][indexTwo]==0:
                    # itemBasketDictionary[itemOneName][itemTwoName] = itemTwo['count']
                    itemBoughtWithOtherItemMatrix[indexOne][indexTwo] = itemTwo['count']
                elif itemTwoName != itemOneName and itemBoughtWithOtherItemMatrix[indexOne][indexTwo]>0:
                    # itemBasketDictionary[itemOneName][itemTwoName] += itemTwo['count']
                    itemBoughtWithOtherItemMatrix[indexTwo][indexOne] += itemTwo['count']

    #load item basket dictionary to find items that are bought together
    aNewHope = load_obj("itemBasketDictionary")
    #for items that share customers with item one, compute similarity
    for keyItemOne, valueOne in aNewHope.items():
        indexItemOne = itemIndexDictionary[keyItemOne]
        for keyItemTwo, valueTwo in valueOne.items():
            indexItemTwo = itemIndexDictionary[keyItemTwo]
            if keyItemOne not in itemCosineSimilarityBasketDictionary:
                itemCosineSimilarityBasketDictionary[keyItemOne] = {keyItemTwo: 1 - spatial.distance.cosine(itemBoughtWithOtherItemMatrix[indexItemOne], itemBoughtWithOtherItemMatrix[indexItemTwo])}
            else:
                itemCosineSimilarityBasketDictionary[keyItemOne][keyItemTwo] =  1 - spatial.distance.cosine(itemBoughtWithOtherItemMatrix[indexItemOne], itemBoughtWithOtherItemMatrix[indexItemTwo])


    save_obj(itemCosineSimilarityBasketDictionary, "itemCosineSimilarityBasketDictionary")
    save_obj_pickle(itemCosineSimilarityBasketDictionary, "itemCosineSimilarityBasketDictionary")

#create item basket with which items are bought together and the count as a dictionary
def createItemBasket():
    print("creating Item basket with count of times both products are bought")
    itemBasketDictionary = {}
    #load necessary objects
    itemsAndUsersWhoPurchased = load_obj("uniqueItemsAndCustomers")
    userAndItemsPurchased = load_obj("userItemsPurchased")
    print("okay")

    listOfItems = list(itemsAndUsersWhoPurchased)
    itemBoughtWithOtherItemMatrix = np.zeros((len(listOfItems), len(listOfItems)))

    #parse through all unique items boughts
    for itemOneName, itemOne in itemsAndUsersWhoPurchased.items():
        itemBasketDictionary[itemOneName] = {}
        #parse through all customers who bought the unique item
        for customer in itemOne['customers']:
            #parse through all of the other items purchased by the selected customer
            for itemTwoName, itemTwo in userAndItemsPurchased[str(customer)].items():
                if itemTwoName != itemOneName and itemTwoName not in itemBasketDictionary[itemOneName]:
                    itemBasketDictionary[itemOneName][itemTwoName] = itemTwo['count']
                elif itemTwoName != itemOneName and itemTwoName in itemBasketDictionary[itemOneName]:
                    itemBasketDictionary[itemOneName][itemTwoName] += itemTwo['count']

    save_obj(itemBasketDictionary, "itemBasketDictionary")
    save_obj_pickle(itemBasketDictionary, "itemBasketDictionary")

#get users and their purchases
def getUserPurchases():
    userItemsPurchased={}
    #load file and online retail sheet into data
    xlsx = pd.ExcelFile('Online_retail_Data.xlsx')
    data = pd.read_excel(xlsx, sheet_name='Online Retail')
    print("creating dictionary with key unique userID and with value of dictionary of items bought with stockcode")
    print(len(data))
    for index, row in data.iterrows():
        # print(row['Description'])
        # print(type(row['Description']))
        description = ""
        if isinstance(row['Description'], str):
            description = row['Description'].rstrip()
            description = row['Description'].lstrip()
        else:
            description = row['Description']

        if row['CustomerID'] not in userItemsPurchased:
            userItemsPurchased[row['CustomerID']] = {description: {'stockCode': row['StockCode'], 'count': row['Quantity']}}
        elif description not in userItemsPurchased[row['CustomerID']]:
            userItemsPurchased[row['CustomerID']][description] = {'stockCode': row['StockCode'], 'count': row['Quantity']}
        else:
            userItemsPurchased[row['CustomerID']][description]['count'] +=row['Quantity']
    save_obj(userItemsPurchased, "userItemsPurchased")
    save_obj_pickle(userItemsPurchased, "userItemsPurchased")

#get items and customers who purchased them
def getUniqueItemsAndCustomers():
    items = {}
    xlsx = pd.ExcelFile('Online_retail_Data.xlsx')
    data = pd.read_excel(xlsx, sheet_name='Online Retail')

    #go through excel file
    for index, row in data.iterrows():
        description = ""
        if isinstance(row['Description'], str):
            description = row['Description'].rstrip()
            description = row['Description'].lstrip()
        else:
            description = row['Description']
        if math.isnan(row['CustomerID']):
            if description in items:
                items[description]['count'] += row['Quantity']
            else:
                items[description] = {'customers':[],'stockCode': row['StockCode'], 'count': row['Quantity']}
        elif description not in items:
            items[description] = {'customers':[row['CustomerID']],'stockCode': row['StockCode'], 'count': row['Quantity']}
        elif row['CustomerID'] not in items[description]['customers']:
            items[description]['customers'].append(row['CustomerID'])
            items[description]['count'] += row['Quantity']
        else:
            items[description]['count'] += row['Quantity']

        if description == "PAPER CRAFT , LITTLE BIRDIE":
            print(row)
            print(items[description])
    save_obj(items, "uniqueItemsAndCustomers")
    save_obj_pickle(items, "uniqueItemsAndCustomers")


def main():
#    print("starting user purchases")
#    getUserPurchases()
#    
#    print("starting unique items and customers")
#    getUniqueItemsAndCustomers()
#
#    print("starting item basket")
#    createItemBasket()
#
#    print("calculate similarity starting")
#    too computationally heavy
#    calculateItemSimilarityUsingJaccardIndex()
#    better
#    calculateItemSimilarityUsingCosineSimilarity()
    getProductsBoughtTogether("50'S CHRISTMAS GIFT BAG LARGE")


if __name__== "__main__":
  main()
