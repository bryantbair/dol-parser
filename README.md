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