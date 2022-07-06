'''
Bryant Bair
DFS 510-81
March 5, 2021
Delivery Optimization GEO result IP Scan ver 0.1
This script examines the text file output from the 'Get-DeliveryOptimizationLog | Out-File -FilePath .\DOL.txt -Encoding ascii' PowerShell Cmd-Lets 
and produces a list of ExternalIP addresses by searching for the text string "GEO result" and extracting the IP address and country code and places
that information into an 'in-memory' sqlite database/table.  A secondary table is created and holds the IP address and associated date/time stamps.
The script outputs the list of IPs, country code, and the number of occurances for each IP address by default.  If an additional argument is passed
with one of the IP addresses, the script will also output the list of date/time stamps at which that IP was seen.

The list of ip addresses produced by this script could be used by an examiner to identify where a system was used by taking the output and identifying the 
internet service provider that owns the IP address and providing them with a subpoena to identify the subscriber information.  The IP addresses also provide 
rough geolocation as they may be searching for the IP address on a site such as https://whatismyipaddress.com/ip-lookup.  Further development of the script 
could automate this process.

This script will run with or without prettytable, the results will be formatted a bit differently.
'''

import argparse       # Python Standard Library argument parsing
import os             # Python OS or Filesystem Access 
import time           # Python Time Library
import re             # Python Regular Expression Library
import sqlite3        # Python Standard Library sqlite3


# Check if prettytable is available, if not set PRETTY to False to use simple text printing
try:
    from prettytable import PrettyTable
    PRETTY = True
except:
    PRETTY = False
    
# create database connection, holding database in memory
conn = sqlite3.connect(':memory:')
# create database cursor
c = conn.cursor()

class LogExaminer:    
    # The next two commands create tables to store results. The first, ipAdd stores IP address, country code and the number of occurances.
    # The second table stores the same IP address along with the date/time stamp for each occurance.
    c.execute("""CREATE TABLE IF NOT EXISTS ipAdd (
                 geoIP TEXT PRIMARY KEY, country TEXT, occurances INTEGER)
               """)
    c.execute("""CREATE TABLE IF NOT EXISTS timeTracker (id INTEGER PRIMARY KEY, geoIP TEXT, timeDateGroup TEXT)""")
    
    
    def __init__(self):
        self.ARGS = self.ParseCommandLine()
        self.SOURCE = os.path.abspath(self.ARGS.source)
        
       
    def ValidateFile(self,theFile):
        # Validate the path is a file
        if not os.path.isfile(theFile):
            raise argparse.ArgumentTypeError('File does not exist')
        
        # Validate the file is readable
        if os.access(theFile, os.R_OK):
           return theFile
        
    def ParseCommandLine(self):
        ''' parse the command line arguments '''
    
        parser = argparse.ArgumentParser(
            description='Delivery Optimization Log .etl Processor .. Python 3.x Version March 2021',
            epilog="""On first run, provide the -s argument for the text of the file produced by running \"Get-DeliveryOptimizationLog | Out-File -FilePath .\DOL.txt -Encoding ascii\" in
            PowerShell.  If after running the file you would like to output the date and time for each occurance of a partiuclar IP address, enter that IP address
            with no leading zeros (exactly as it appears in the first results) with the -a argument.\n\n
            """)
        
        parser.add_argument('-s', '--source', type= self.ValidateFile, help='specify source file for log', required=True)        
        parser.add_argument('-a', '--address', help='Input ip address to show all occurance. Format as xxx.xxx.xxx.xxx with no leading zeros')
        parsedArguments = parser.parse_args()   
    
        return parsedArguments
    
    def ProcessFile(self):
        args = self.ParseCommandLine()
        
        # create dictionary to store unique geo IPs and counts
        resultsDict = {}
        # create a counter which will be used as the id column for the timeTracker table such that each ExternalIP address instance is numbered sequentially
        foundCount = 0
        # open source file
        with open(args.source) as logFile:
            # create list and place each line of source file into the list as a string
            logSplitList=[]
            for eachLine in logFile:
                logSplitList.append(eachLine)            
            
            # iterate through list and identify instances containing a GEO response.       
            for index, eachRow in enumerate(logSplitList):
                if 'GEO response' in eachRow:                 
                    # Extract the formatted IP address from the longer string and assign it to ipAddress
                    ipAddress = re.findall("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}", eachRow)
                    # Extract the country code 
                    countryCode = re.findall("\"CountryCode\":\"\w{2}", eachRow)
                    # make assign the first item in the list to geo (there is probably a more elegant solution to solve this)
                    geo = ipAddress[0]
                    # Assign the line containing time/date/group to variable based on standard position five rows before the 'GEO response'
                    timeFullLine = logSplitList[index-5]
                    # Split just time/date/group from the remainder of the linline                    
                    timeOnly = timeFullLine.split(": ", 1)[1][:-1]
                    # check if the IP address is already in the result dictionary.  If so, increment the occurances field for that IP in ipAdd table.
                    if geo in resultsDict:
                        # this counter increments in either case within the if/else statement to ensure each iteration is assigned a number                        
                        foundCount += 1
                        # insert appropriate fields into both tables. The timeTracker insert is the same for both the if and else.
                        with conn:
                            c.execute("""UPDATE ipAdd SET occurances = (occurances + 1) WHERE geoIP = :ipAddress""", {'ipAddress': geo})
                            c.execute("INSERT INTO timeTracker VALUES (:foundCount, :geoIP, :timeDateGroup)", {'foundCount': foundCount, 'geoIP': geo, 'timeDateGroup': timeOnly}) 
                        resultsDict[geo] += 1
                    else: 
                        resultsDict[geo] = 1
                        foundCount += 1
                        # insert appropriate fields into tables.  The else is executed on the first sighting of a particular IP.
                        with conn: 
                            c.execute("INSERT INTO ipAdd VALUES (:geoIP, :country, :occurances)", {'geoIP': geo, 'country': countryCode[0][15:17], 'occurances': 1})
                            c.execute("INSERT INTO timeTracker VALUES (:foundCount, :geoIP, :timeDateGroup)", {'foundCount': foundCount, 'geoIP': geo, 'timeDateGroup': timeOnly})                 
        return 
    
    def PrettyResults(self):            
            #Create Pretty Table with Heading for main table with IP Address, Country Code, and Occurances            
            t = PrettyTable(['IP Address','Country Code','Occurances'])
            # Select all rows from main table
            with conn:        
                c.execute("SELECT * FROM ipAdd")
                results = c.fetchall()             
            for entry in results:
                #add each row to pretty table
                t.add_row( [entry[0], entry[1], entry[2]] )  
            t.align = "l" 
            # place table into single string
            tabularResults = t.get_string()
            # print pretty table
            print(tabularResults)  
    
    def DumpResults(self):
        # Print ipAdd table data into clusters of info
        with conn:        
            c.execute("SELECT * FROM ipAdd")
            results = c.fetchall()         
        for eachResult in results:
            print("="*45)
            print("IP:            ", eachResult[0])
            print("Country Code:  ", eachResult[1])
            print("Occurances:    ", eachResult[2])
    
    def SpecifiedResultsPretty(self, address):
        # Create Pretty Table with entries with selected IP address each date/time group where it was seen.        
        t = PrettyTable(['#','IP Address', 'Date/Time'])
        # Select all rows from rows from timeTracker table that match specified IP address
        with conn:        
            c.execute("""SELECT * FROM timeTracker WHERE geoIP = :address""", {'address': address})            
            results = c.fetchall()
        recordCount = 1
        for entry in results:
            #add each row to pretty table
            t.add_row( [recordCount, entry[1], entry[2]] )  
            recordCount +=1
        t.align = "l" 
        #add table data to single formatted string
        tabularResults = t.get_string()
        #print table
        print(tabularResults) 
    
    def SpecifiedResultsDump(self, address):
        # Dump results
        # Select all rows from rows from timeTracker table that match specified IP address
        with conn:        
            c.execute("""SELECT * FROM timeTracker WHERE geoIP = :address""", {'address': address})            
            results = c.fetchall() 
            recordCount = 1
            #print heading
            print('+----+---------------+--------------------------+')
            print('| #  | IP Address    | Date/Time                |')
            print('+----+---------------+--------------------------+')           
            # print each row to match heading
            for entry in results:
                print('|' + '{:3d}'.format(recordCount)+' | ' + entry[1] + ' | ' + '%24s' % entry[2] + ' |')
                recordCount += 1
            print('+----+---------------+--------------------------+')
                
                
if __name__ == '__main__':

    LOG_EXAMINER_VERSION = '1.0 Feb 2021 Python 3.x and 2.x Version'

    # instantiate a LogExaminer
    examinerObject = LogExaminer()
    # create argument variable
    args = examinerObject.ARGS
    # print any user provided Input
    print("User Input")
    print("----------")
    print("File Selection: ", examinerObject.SOURCE)
    
    # Traverse the file system directories and place data in sqlite3 database in memory
    examinerObject.ProcessFile()
    
    # if pretty table is installed, call PrettyResults to output ipAdd, otherwise perform simple dump
    if PRETTY:
        ''' if prettytable library available '''
        examinerObject.PrettyResults()
    else:
        ''' otherwise a simple dump '''
        examinerObject.DumpResults()

    # if -a argument is passed, call SpecifiedResultsPretty to output matching IP and date/time stamps, otherwise perform simple dump.
    if args.address:
        print('Results for ' + args.address) 
        if PRETTY:
            ''' if prettytable library available '''
            examinerObject.SpecifiedResultsPretty(args.address)
        else:
            ''' otherwise a simple dump '''
            examinerObject.SpecifiedResultsDump(args.address)        
    print('Program Terminated Normally')
    
print("Done")
