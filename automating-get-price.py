import bs4 as bs
import pandas as pd
import datetime as dt
import quandl
import pickle
import requests
import os

import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
style.use('ggplot')

# Get the list of SP500 Company with beautifulsoup
def save_sp500_tickers():


    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class':'wikitable sortable'})

    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        tickers.append(ticker)

    with open('sp500tickers.pickle','wb') as f:
        pickle.dump(tickers, f)

    return tickers

##save_sp500_tickers()
    
def get_data_from_quandl(reload_sp500=False):
    """
    Get data from Quandl and save locally as .csv file
    """

    if reload_sp500:
        tickers = save_sp500_tickers()
    else:
        with open('sp500tickers.pickle','rb') as f:
            tickers = pickle.load(f)

    if not os.path.exists('stock_dfs'):
        os.makedirs('stock_dfs')

    api_key = open('quandlapikey.txt','r').read()
    quandl.ApiConfig.api_key = api_key
    
    startdate = dt.datetime(2010,1,1)
    enddate = dt.datetime.now()

    for ticker in tickers:
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)):
            df = quandl.get_table('WIKI/PRICES', ticker=ticker,
                                  qopts = {'columns': ['ticker', 'date','open','high','low','close','volume','adj_close']},
                                  date = {'gte':startdate, 'lte':enddate},
                                  paginate=True)

            df.reset_index(inplace=True)
            df.set_index('date', inplace=True)
            df.drop(['None','ticker'], axis=1, inplace=True)
            df.to_csv('stock_dfs/{}.csv'.format(ticker))
        else:
            print("Already have {}".format(ticker))

##get_data_from_quandl()


def compile_data():
    """
    Combining stock price into one data frame
    """
    with open('sp500tickers.pickle','rb') as f:
        tickers = pickle.load(f)

    main_df = pd.DataFrame()

    for count, ticker in enumerate(tickers):
        df = pd.read_csv('stock_dfs/{}.csv'.format(ticker))
        df.set_index('date', inplace=True)

        df.rename(columns={'adj_close': ticker}, inplace=True)
        df.drop(['open','high','low','close','volume'], axis=1, inplace=True)

        if main_df.empty:
            main_df = df
        else:
            main_df = main_df.join(df, how='outer')

        if count % 10 == 0:
            print(count)

    print(main_df.head())
    main_df.to_csv('sp500_joined_closes.csv')

##compile_data()

def visualize_data():

    df = pd.read_csv('sp500_joined_closes.csv')

    df_corr = df.corr()

    data1 = df_corr.values

    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111)

    heatmap1 = ax1.pcolor(data1, cmap=plt.cm.RdYlGn)
    fig1.colorbar(heatmap1)

    # Set xtick and ytick so we can know which company are
    ax1.set_xticks(np.arange(data1.shape[0]) + 0.5, minor=False)
    ax1.set_yticks(np.arange(data1.shape[1]) + 0.5, minor=False)

    # flip axis to easier to read
    ax1.invert_yaxis()
    ax1.xaxis.tick_top()

    # add company name to the nameless ticks
    column_labels = df_corr.columns
    row_labels = df_corr.index
    ax1.set_xticklabels(column_labels)
    ax1.set_yticklabels(row_labels)

    # rotate the axis to vertical for easy reading, set colormap range is (-1,1)
    plt.xticks(rotation=90)
    heatmap1.set_clim(-1,1)
    plt.tight_layout()
    plt.show()
    

visualize_data()

        
