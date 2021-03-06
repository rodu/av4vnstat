#Setup instructions

##Installing and initializing vnstat

First of all it is necessary to install vnstat.
On a Debian based Linux distribution (like Ubuntu is) this is done with:

$ sudo apt-get install vnstat

Next you need to initialize the vnstat db and inform vnstat about the network
card you want to record the traffic from.

Note: We are not talking about network traffic sniffing!
      See the vnstat manual for details or visit the vnStat project home page at
      http://humdi.net/vnstat/

Assuming you want to monitor the eth1 (any interface can be monitored giving the
proper name) you need to issue:

$ sudo vnstat -u -i eth1

At this point vnstat will start to monitor the network interface at regular
intervals and will build its own data file.

To show the data grabbed so far you can give from the terminal the command:

$ vnstat -i eth1


##Configuration

You should update the program configuration in the file that comes with
the download:

av4vnstat.cfg


In there you need to set some valid parameters. You need to set a value for the
install folder:

INSTALL_FOLDER=[your install folder path]

This is an indication needed for the program to work.


You need to change the value for the network card you are monitoring:

NETWORK_CARD=ppp0

Give the proper name (eg. eth0 or eth1). The indication you give here
for the network card must match the indication you gave above to vnstat,
during the initialization phase.

Note:
    This version the program can handle only one network card to show
    data for. In the future the support for more cards can be added.


##Generating the javascript data

Once vnstat is installed and enough data have been collected (to be shown)
you can execute the Python script to create the JS dataset.

From the command line move to the 'src' folder under your install path:

$ cd [ your install folder path ]/av4vnstat/src

Then give:

$ python av4vnstat_run.py

This will generate a javascript file but you wont see any output now.


##Opening the application

To open the Javascript web app you need to open in a browser the file:

[ your install folder path ]/av4vnstatweb/av4vnstat.html

At this point you should be able to see your data.

You can also launch the example.html in the browser to see what the result could
look like.


##Automating the data generation

You can create a cron entry to run the python script on a schedule
time interval. To do this you can create an entry in the crontab where the script
is executed on the first minute for every hour.

$ crontab -e

will open the cron editor and in there you can add a line like:

1 * * * * [ /home/pluto ]/av4vnstat/av4vnstat/src/av4vnstat_run.py

Note the path needs to be changed to point to the python script properly.
In the example we assume to have a folder named run under the pluto's home.

For more info about crontab synstax: $ man 5 crontab

Once all this is done and vnstat has enough data to show you can run
the av4vnstat.html (under the folder av4vnstatweb) and see the results.

Note:
    A working folder is created when running the program under the user
    home. The folder name will be: ~/.av4vnstat
    
    In the working folder will be created:
        - a log file in case of errors
        - the vnstat db dump to be parsed


If something goes wrong you can enable debug messages in the browser console by
changing the value of the DEBUG constant in the Javascript to true.

find:

// Set this to true to see error messages in the browser web console
DEBUG: false,

in:

av4vnstatweb/js/vnstat.js

