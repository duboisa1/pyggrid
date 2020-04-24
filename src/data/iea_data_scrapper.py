import requests
import pandas as pd
import logging
import time
import os
import numpy as np


class DataScrapper:

    def __init__(self):
        logging.info("Building DataScrapper")
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data/")
        print(self.data_dir)
        self.countries_dict = pd.read_csv(f"{self.data_dir}countries-codes.csv", index_col="Code")

    def iea_electricity_consumption(self, countries, start_year, end_year):

        years = list(range(start_year, end_year+1))
        for country in countries:
            print(country)
            iea_country = self.countries_dict.loc[country]['IAE']
            production = pd.DataFrame(columns=["Electricity Consumption (GWh)"], index=years)
            for year in range(start_year, end_year+1):
                url = f"https://api.iea.org/stats/?year={year}&countries={iea_country}&series=ELECTRICITYANDHEAT"
                print(url)
                time.sleep(1)

                # Get the html content of the page
                table = requests.get(url).json()
                for line in table:
                    if line["flowLabel"] == "Final consumption" and line["productLabel"] == "Electricity":
                        value = line['value']
                        if value == 0:
                            value = np.nan
                        production.loc[year, "Electricity Consumption (GWh)"] = value
                        break
            production.to_csv(f"{self.data_dir}load/source/iea/{country}.csv")

    def iea_electricity_production(self, countries, start_year, end_year):

        years = list(range(start_year, end_year+1))
        for country in countries:
            print(country)
            iea_country = self.countries_dict.loc[country]['IAE']
            production = pd.DataFrame(columns=["Electricity Production (GWh)"], index=years)
            for year in range(start_year, end_year+1):
                url = f"https://api.iea.org/stats/?year={year}&countries={iea_country}&series=ELECTRICITYANDHEAT"
                print(url)
                time.sleep(1)

                # Get the html content of the page
                table = requests.get(url).json()
                for line in table:
                    if line["flowLabel"] == "Total production" and line["productLabel"] == "Electricity":
                        value = line['value']
                        if value == 0:
                            value = np.nan
                        production.loc[year, "Electricity Production (GWh)"] = value
                        break
            production.to_csv(f"{self.data_dir}production/source/iea/{country}.csv")

    def iea_co2_by_electricity_and_heat(self, countries):

        for country in countries:
            production = pd.DataFrame(columns=["CO2 from electricity and heat producers (MT)"])
            iea_country = self.countries_dict.loc[country]['IAE']
            url = f"https://api.iea.org/stats/indicator/CO2BySector?countries={iea_country}"
            print(url)
            time.sleep(1)

            # Get the html content of the page
            table = requests.get(url).json()
            for line in table:
                if line['flowLabel'] == 'Electricity and heat producers':
                    production.loc[int(line['year']), "CO2 from electricity and heat producers (MT)"] = line['value']

            print(production)

            production.to_csv(f"{self.data_dir}emission/source/iea/{country}.csv")


if __name__ == '__main__':

    ds = DataScrapper()

    countries = ["AL", "AT", "BA", "BE", "BG", "CH", "CZ", "DE", "DK", "EE", "GR", "ES", "FI", "FR", "HR",
                 "HU", "IE", "IT", "LT", "LU", "LV", "ME", "MK", "NL", "NO", "PL", "PT", "RO",
                 "RS", "SE", "SI", "SK", "GB"]

    ds.iea_electricity_consumption(countries, 1990, 2017)
