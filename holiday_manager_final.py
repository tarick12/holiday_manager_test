from dataclasses import dataclass, field
import json
from datetime import datetime

from bs4 import BeautifulSoup
import requests

from config import weather_key
from config import JSON_loc
from config import scraped
from config import scraped_data


@dataclass
class Holiday:
    name: str
    date: datetime      
    
    def getWeatherForecast(self, zip):
        response = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?zip={zip},us&appid={weather_key}')

        for node in json.loads(response.text)['list']:
            if datetime.strptime(self.date, '%Y-%m-%d').date() == datetime.fromtimestamp(node['dt']).date():
                return node['weather'][0]['description']

        return 'No weather data found.'
          
@dataclass           
class HolidayList:
    innerHolidays: list = field(default_factory = list)
   
    def addHoliday(self, holiday):
        self.innerHolidays.append(holiday)

    def findHoliday(self, name, year):
        if year != False:
            return any(holiday.name == name and str(datetime.strptime(holiday.date, '%Y-%m-%d').year) == year for holiday in self.innerHolidays)

        else:
            return any(holiday.name == name for holiday in self.innerHolidays)

    def removeHoliday(self, name, year):
        if year == 'ALL':
            self.innerHolidays = list(filter(lambda holiday: holiday.name != name, self.innerHolidays))

        else:
            self.innerHolidays = list(filter(lambda holiday: holiday.name != name or str(datetime.strptime(holiday.date, '%Y-%m-%d').year) != year, self.innerHolidays))

    def readJSON(self):
        file = open(JSON_loc)
        for holiday in json.load(file)['holidays']:
            self.innerHolidays.append(Holiday(holiday['name'], holiday['date']))

        file.close()

    def saveToJSON(self):
        holidays = {'holidays':[]}

        for holiday in self.innerHolidays:
            holidays['holidays'].append({'name':holiday.name, 'date':holiday.date})

        file = open(JSON_loc, 'w')

        json.dump(holidays, file)

        file.close()
    
    def filterHolidaysByWeek(self, year, week):
        if week == 'CURRENT':
            return list(filter(lambda holiday: str(datetime.strptime(holiday.date, '%Y-%m-%d').year) == year and str(datetime.strptime(holiday.date, '%Y-%m-%d').strftime('%V')) == datetime.now().strftime('%V'), self.innerHolidays))

        else:
            if len(week) == 1:
                week = f'0{week}'

            return list(filter(lambda holiday: str(datetime.strptime(holiday.date, '%Y-%m-%d').year) == year and str(datetime.strptime(holiday.date, '%Y-%m-%d').strftime('%V')) == week, self.innerHolidays))

def scrapeHolidays(holidayList):
    for year in range(2022 - 2, 2022 + 3):
        response = requests.get(f'https://www.timeanddate.com/holidays/us/{year}')
        tbody = BeautifulSoup(response.text, 'html.parser').find('table', attrs = {'id':'holidays-table'}).find('tbody')

        for row in tbody.find_all('tr'):
            if len(row.find_all()) != 0:
                date = datetime.strftime(datetime.strptime(f'{row.th.string} {year}', '%b %d %Y'), '%Y-%m-%d')
                name = row.select_one('td > a').string

                holidayList.addHoliday(Holiday(name, date))

    print('Scraping successful.\n')

def startupMsg(holidayCount):
    print('Holiday Manager')
    print('===============')
    print(f'There are {holidayCount} holidays stored in the system.\n')

def menuOptions():
    print('Holiday Menu')
    print('=============')
    print('1. Add a Holiday')
    print('2. Remove a Holiday')
    print('3. Save Holiday List')
    print('4. View Holidays')
    print('5. Exit')

def main():
    holidayList = HolidayList()

    holidayList.readJSON()

    if not scraped:
        scrapeHolidays(holidayList)

        holidayList.saveToJSON()

        file = open(scraped_data, 'r')
        file.seek(15)
        lines = file.readlines()
        lines.insert(0, 'scraped data:')

        file = open(scraped_data, 'w')
        file.write(''.join(lines))

    startupMsg(len(holidayList.innerHolidays))

    userExited = False

    while not userExited:
        menuOptions()

        menuOption = input('')

        if menuOption == '1':
            print('\nAdd a Holiday')
            print('=============')

            validName = False
            while not validName:
                name = input('Holiday: ')

                if len(name) != 1:
                    validName = True

                else:
                    print('Holiday name too short.\n')

            validDate = False
            while not validDate:
                date = input('Date [YYYY-MM-DD]: ')

                try:
                    datetime.strptime(date, '%Y-%m-%d')

                    if int(date[0:4]) > 1999 and int(date[0:4]) < 2100:

                        holiday = Holiday(name, date)
                        
                        if holiday not in holidayList.innerHolidays:
                            holidayList.addHoliday(holiday)
                            print(f'{name} ({date}) has been successfully added.\n')

                            validDate = True

                        else:
                            print('Holiday already exists.\n')
                            
                            validDate = True

                    else:
                        print('Year out of range. Please try again.\n')

                except ValueError:
                    print('Invalid date. Please try again.\n')

        elif menuOption == '2':
            print('\nRemove a Holiday')
            print('================')

            validYear = False
            while not validYear:
                year = input("Year [type 'all' to remove all instances]: ")

                if year.upper() == 'ALL':
                    validYear = True

                elif year.isnumeric():
                    if int(year) > 1999 and int(year) < 2100:
                        validYear = True

                    else:
                        print('Year out of range. Please try again.\n')

                else:
                    print('Invalid date. Please try again.\n')

            validName = False
            while not validName:
                name = input('Holiday: ')

                if year.upper() == 'ALL':

                    if holidayList.findHoliday(name, False):
                        holidayList.removeHoliday(name, year.upper())
                        print(f'{name} has been successfully removed from the holiday list.\n')
                        validName = True

                    else:
                        print('Holiday could not be found.\n')

                else:

                    if holidayList.findHoliday(name, year):
                        holidayList.removeHoliday(name, year)
                        print(f'{name} has been successfully removed from the holiday list.\n')
                        validName = True

                    else:
                        print('Holiday could not be found.')

        elif menuOption == '3':
            print('\nSave Holiday List')
            print('====================')

            validChoice = False
            while not validChoice:
                choice = input('Are you sure you want to save your changes? [y/n]: ').lower()

                if choice == 'y':
                    holidayList.saveToJSON()
                    print('\nYour changes have been saved.\n')
                    validChoice = True

                elif choice =='n':
                    print('')
                    validChoice = True

                else:
                    print('Please enter "y" or "n".\n')

        elif menuOption == '4':
            print('\nView Holidays')
            print('===============')

            validYear = False
            while not validYear:
                year = input("Year: ")

                if year.isnumeric():
                    if int(year) > 1500 and int(year) < 2500:
                        validYear = True

                    else:
                        print('Year out of range. Please try again.\n')

                else:
                    print('Invalid date. Please try again.\n')

            validWeek = False
            while not validWeek:
                if year == str(2022):
                    week = input('Which week? #[1-52, type "current" to view current week]: ')

                else:
                    week = input("Week #[1-52]: ")
                
                if week.isnumeric():
                    if int(week) >= 1 and int(week) <= 52:
                        print('')
                        validWeek = True

                    else:
                        print('Week out of range.\n')

                elif week.upper() == 'CURRENT' and year == str(2022):
                    validChoice = False
                    while not validChoice:
                        weatherChoice = input('Display weather [y/n]?: ').lower()

                        if weatherChoice == 'y':
                            validZip = False
                            while not validZip:
                                zip = input('Zip code: ')

                                if zip.isnumeric() and len(zip) == 5:
                                    print('')
                                    validZip = True

                                else:
                                    print('Please enter a valid zip code.\n')

                            validChoice = True

                        elif weatherChoice =='n':
                            validChoice = True

                        else:
                            print('Please enter a valid choice.\n')

                    validWeek = True

                else:
                    print('Invalid week. Please try again.\n')

            holidaysByWeek = holidayList.filterHolidaysByWeek(year, week.upper())

            if len(holidaysByWeek) == 0:
                print(f'Holidays for {year} Week {week}.')
                print('=========================')
                print('No holidays during this week.\m')
            
            elif week.upper() == 'CURRENT' and weatherChoice == 'y':
                print('Holidays and Weather for the Current Week')
                print('=========================================')

                for holiday in holidaysByWeek:
                    print(f'{holiday.name} ({holiday.date}) - {holiday.getWeatherForecast(zip)}\n')


            else:
                print(f'Holidays for {year} Week {week}.')
                print('=================================')

                for holiday in holidaysByWeek:
                    print(f'{holiday.name} ({holiday.date})\n')

        elif menuOption == '5':
            tempHolidayList = HolidayList()

            tempHolidayList.readJSON()

            if tempHolidayList.innerHolidays != holidayList.innerHolidays:
                changes = True

            else:
                changes = False

            validChoice = False
            while not validChoice:
                print('')
                
                if changes:
                    print('Your changes will be lost.\n')
                
                choice = input('Are you sure you want to exit [y/n]?: ').lower()

                if choice == 'y':
                    print('\nGoodbye!')
                    userExited = True
                    validChoice = True

                elif choice =='n':
                    print('')
                    validChoice = True

                else:
                    print('Please enter a valid choice.\n')

        else:
            print('Please enter a valid menu choice.\n')

if __name__ == '__main__':
    main()