import os
import math
import json
import secret
import pprint
import requests
import mysql.connector


FMP_API_KEY = secret.FMP_API_KEYS
DB_PW = secret.DB_PASSWORDD
NaN = -9999999

class fmp:
    def __init__(self) -> None:
        self.mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password=DB_PW
        )

        self.mycursor = self.mydb.cursor()
        self.mycursor.execute("CREATE DATABASE IF NOT EXISTS fmp")
        self.mycursor.execute("USE fmp")

    def load_sp500_symbol_list(self):

        if os.path.exists('./sp500_symbols.json'):
            fp = open("./sp500_symbols.json", "r")
            data = json.load(fp)
            print(len(data['symbols']))
            return data['symbols']

        out_dict = {}
        symbols = []
        sp500 = requests.get(f"https://financialmodelingprep.com/api/v3/sp500_constituent?apikey={FMP_API_KEY}").json()

        for data in sp500:
            symbols.append(data['symbol'])

        out_dict['symbols'] = symbols

        with open('./sp500_symbols.json', 'w') as fp:
            json.dump(out_dict, fp)

        return symbols

    def company_profile(self, symbol: str):

        self.mycursor.execute("""CREATE TABLE IF NOT EXISTS company_profile (\
        id INT AUTO_INCREMENT PRIMARY KEY, \
        name VARCHAR(255), \
        symbol VARCHAR(20), \
        exchange VARCHAR(255), \
        sector VARCHAR(255), \
        industry VARCHAR(255), \
        marketCap float,
        numEmployees int)""")

        data = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{symbol.upper()}?apikey={FMP_API_KEY}").json()[0]

        name = data['companyName']
        symbol = data['symbol']
        exchange = data['exchangeShortName']
        sector = data['sector']
        industry = data['industry']
        marketCap = data['mktCap']
        numEmployees = data['fullTimeEmployees']

        sql = """
        INSERT INTO company_profile \
        (name, symbol, exchange, sector, industry, marketCap, numEmployees) \
        VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        val = (name, symbol, exchange, sector, industry, float(marketCap), int(numEmployees))

        self.mycursor.execute(sql,val)
        self.mydb.commit()

    def ratios(self, symbol: str):
        self.mycursor.execute("""CREATE TABLE IF NOT EXISTS ratios (\
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(255),
            revenue_per_share_fiveY_growth float,
            gross_profit_margin float,
            roe float,
            eps_growth float,
            div_yield float,
            div_per_share float,
            dps_fiveY_growth float)""")

        ratio_ttm = requests.get(f"https://financialmodelingprep.com/api/v3/ratios-ttm/{symbol.upper()}?apikey={FMP_API_KEY}").json()[0]

        div_yield = ratio_ttm['dividendYieldTTM']
        if not div_yield: return
        div_per_share = ratio_ttm['dividendPerShareTTM']
        if not div_per_share: return
        gross_profit_margin = ratio_ttm['grossProfitMarginTTM']
        roe = ratio_ttm['returnOnEquityTTM']

        growth = requests.get(f"https://financialmodelingprep.com/api/v3/financial-growth/{symbol.upper()}?period=quarter&limit=20&apikey={FMP_API_KEY}").json()[0]

        eps_growth = growth['epsgrowth']
        if eps_growth <= 0: return
        dps_fiveY_growth = growth['fiveYDividendperShareGrowthPerShare']
        if dps_fiveY_growth <= 0: return
        revenue_per_share_fiveY_growth = growth['fiveYRevenueGrowthPerShare']
        if revenue_per_share_fiveY_growth <= 0: return

        sql = """
        INSERT INTO ratios \
        (symbol, revenue_per_share_fiveY_growth, gross_profit_margin, roe, eps_growth, div_yield, div_per_share, dps_fiveY_growth) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

        val = (
            symbol,
            float(revenue_per_share_fiveY_growth),
            float(gross_profit_margin),
            float(roe),
            float(eps_growth),
            float(div_yield),
            float(div_per_share),
            float(dps_fiveY_growth))

        self.mycursor.execute(sql,val)
        self.mydb.commit()

    def drop_all_databases(self):

        self.mycursor.execute("SHOW DATABASES")
        excluded = ['sys', 'information_schema', 'performance_schema', 'mysql']
        db_names = []

        for name in self.mycursor:
            if name[0] not in excluded:
                db_names.append(name[0])

        for name in db_names:
            self.mycursor.execute(f"DROP DATABASE {name}")
            self.mydb.commit()


# mycursor.execute("ALTER TABLE company_profile ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY")

# mycursor.execute("ALTER TABLE company_profile ADD COLUMN numEmployees INT")

# mycursor.execute("ALTER TABLE company_profile MODIFY COLUMN marketCap float")





if __name__ == '__main__':

    # myfmp = fmp()

    # myfmp.drop_all_databases()

    myfmp = fmp()

    symbols = myfmp.load_sp500_symbol_list()

    for symbol in symbols:
        myfmp.company_profile(symbol)
        print(f"{symbol}: profile completed")
        myfmp.ratios(symbol)
        print(f"{symbol}: ratio completed")





