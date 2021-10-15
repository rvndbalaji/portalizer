import requests
from datetime import date, timedelta, datetime
from time import sleep
import time
import pandas as pd
import os
import browser_cookie3
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#=================  SET THE FOLLOWING INPUTS   ================= 

start_date = date(2020,12,1)                                    #Date from which stocks should be fetched
end_date = date(2021,10,15)                                     #Date until which stocks should be fetched
xsrf_token = "Jjzo2N3Sfz5bGHZY4ZRBojrWhsfn77HV"                 #Token is present in console.zerodha cookies 'public_token'
export_filename = "holdings"                                    #File name without extension
skip_download_read_json = True
#=================  SET THE ABOVE INPUTS   ================= 


delta = timedelta(days=1)
cookies = browser_cookie3.chrome(domain_name='.zerodha.com')
full_data = {} 
prev_stock = {}
start = time.time()

def getHeaders():
    headers= {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36", 
        "Accept-Encoding":"gzip, deflate", 
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
        "DNT":"1",
        "Connection":"close", 
        "Upgrade-Insecure-Requests":"1",
        "x-csrftoken": xsrf_token
    }
    return headers

def cleanAndGroupName(stock_name):
    stock_name = stock_name.replace('6','')
    stock_name = stock_name.split('-')[0]
    return stock_name

def requestStockData(start_date):
    r = requests.get("https://console.zerodha.com/api/reports/holdings/portfolio?date=" + str(start_date.strftime("%Y-%m-%d")), verify=False, headers=getHeaders(), cookies=cookies)
    json_result = r.json()
    if json_result['status']=='error':
        print("\n\nError : " + json_result['message'] + "\n\n")
        exit()
    return json_result['data']

def parseStockForDate(stock, cur_date):
    stock_name = str(stock['tradingsymbol'])
    stock_name = cleanAndGroupName(stock_name)
    stock_profit_pc = stock['unrealized_profit_percentage']
    
    #If the profit is None, its likely a trade holiday, so use the previous day's profit
    if stock_profit_pc is None: 
        if stock_name in prev_stock:
            stock_profit_pc = prev_stock[stock_name]
        else:
            stock_profit_pc = 0

    if(cur_date not in full_data):
        full_data[cur_date] = {}

    full_data[cur_date] = {**full_data[cur_date], **{stock_name:stock_profit_pc}}

    prev_stock[stock_name] = stock_profit_pc

def exportJson(data):
    print("\n\nPreparing JSON for future use : stocks.json")
    with open(export_filename + '.json', 'w') as outfile:
        json.dump(data, outfile)

def exportCSV(data_frame):
    print("\n\nWriting to CSV file : stocks.csv")
    data_frame.to_csv(export_filename + '.csv')

def exportExcel(data_frame):
    print("\n\nWriting to CSV file : stocks.csv")
    data_frame.to_excel(export_filename + '.xlsx')

if __name__ == "__main__":    

    while start_date <= end_date:
        cur_date = str(start_date.strftime("%d-%m-%Y"))
        print("\n\nQuerying stock for " + cur_date)
        result = requestStockData(start_date)
        status = result['state']
        
        if status == 'PENDING':
            print("PENDING - Retrying...")
            sleep(1)
            continue
        stocks = result['result']['eq']

        for stock in stocks:
            parseStockForDate(stock, cur_date)

        start_date += delta

    #Prepare Pandas DataFrame
    print("\n\nGetting your data ready...")
    df = pd.DataFrame.from_dict(full_data, orient='index')
    df.fillna(0, inplace=True)

    exportJson(full_data)
    exportCSV(df)
    exportExcel(df)

    end = time.time()
    print("\n\nElapsed time : " + str(end-start) + " seconds\n")

