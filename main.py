"""
This module accesses the first energy api and calculates your energy usage between two dates
TODO: Fetch energy prices from the first energy api
"""
import os
import json
from datetime import date, timedelta, datetime
import csv
import requests

CENTS_PER_KILOWATT_PEAK = 33
CENTS_PER_KILOWATT_OFFPEAK = 15.29
CENTS_PER_KILOWATT = 27.29
SOLAR_REBATE = 12
DAILY_CHARGE = 108.79


class EnergyUsage:
    """
    Contains all the goodies for getting this done
    """
    def __init__(self, begin_date, stop_date):
        self.start_date = begin_date
        self.end_date = stop_date
        self.add_days = timedelta(days=1)
        self.usage = 0
        self.usage_peak = 0
        self.usage_offpeak = 0
        self.generated = 0
        self.usage_in_dollaridoos = 0
        self.generated_in_dollaridoos = 0

    def get_api_token(self):
        """
        Handles authentication with first energy using credentials stored in credentials.json
        Stores auth token in token.txt
        """
        if os.path.isfile("credentials.json"):
            with open(file="credentials.json", encoding="utf-8") as f:
                credentials = json.load(f)

            response = requests.post(
                "https://portal-api.1stenergy.com.au/api/users/validate-user",
                data=None,
                json=credentials,
                timeout=60
            )
            print(response.json())
            auth_token = response.json()["result"]["token"]
            with open(file="token.txt", mode="w", encoding="utf-8") as f:
                f.write(auth_token)

        else:
            with open(file="token.txt", encoding="utf-8") as f:
                auth_token = f.read()

        return auth_token

    def get_usage_data(self):
        """"
        Fetches the usage data from the first energy api
        """
        auth_token = self.get_api_token()
        headers = {"Authorization": "Bearer " + auth_token}
        date_increment = self.start_date
        while date_increment <= self.end_date:
            date_as_string = date_increment.strftime("%Y-%m-%d")
            response = requests.get(
                f"https://portal-api.1stenergy.com.au/api/utility/410151/usage-data/download?viewInterval=day&productType=POWER&startDate={date_as_string}",
                headers=headers,
                timeout=60*60
            )
            date_increment += self.add_days

            reader = csv.reader(response.text.split("\n"), delimiter=",")
            next(reader)

            for row in reader:
                row_len = len(row)

                if row_len == 6:
                    self.usage_peak += float(row[4] or 0)
                    self.usage_offpeak += float(row[3] or 0)
                    self.generated += float(row[2])

                elif row_len == 5:
                    if datetime.strptime(row[1], "%Y-%m-%dT%H:%M:%S").date() < date(
                        2023, 2, 1
                    ):
                        self.usage += float(row[3])
                    else:
                        self.usage_offpeak += float(row[3])

                    self.generated += float(row[2])

    def calculate_usage(self):
        """
        Calculates your usage based on the price per kilowatt
        """
        self.usage_in_dollaridoos = (
            (self.usage * CENTS_PER_KILOWATT / 100)
            + (self.usage_peak * CENTS_PER_KILOWATT_PEAK / 100)
            + (self.usage_offpeak * CENTS_PER_KILOWATT_OFFPEAK / 100)
        )
        self.generated_in_dollaridoos = self.generated * SOLAR_REBATE / 100

    def print_usage_data(self):
        """
        Prints the usage data out, with peak / offpeak and generated
        """
        print(f"usage peak: {self.usage_peak}")
        print(f"usage offpeak: {self.usage_offpeak}")
        print(f"generated: {self.generated}")

    def print_calculated_usage(self):
        """
        Print out usage costs
        """
        bill_estimate = (
            self.usage_in_dollaridoos
            - self.generated_in_dollaridoos
            + (((DAILY_CHARGE * (self.end_date - self.start_date).days + 1) / 100))
        )
        print(f"start:{self.start_date}, end:{self.end_date}")
        print(f"days:{(self.end_date - self.start_date).days}")
        print(
            f"daily charge $:{(DAILY_CHARGE * (self.end_date - self.start_date).days+1) / 100}"
        )
        print(f"usage $:{self.usage_in_dollaridoos}")
        print(f"generated $:{self.generated_in_dollaridoos}")
        print(f"bill estimate: {bill_estimate}")


if __name__ == "__main__":
    start_date = date(2023, 1, 1)
    end_date = date(2023, 10, 13)
    energy_usage = EnergyUsage(start_date, end_date)
    energy_usage.get_usage_data()
    energy_usage.calculate_usage()
    energy_usage.print_usage_data()
    energy_usage.print_calculated_usage()
