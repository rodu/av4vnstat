#
# Copyright (C) 2012 Rodu
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from av4vnstat.util.Config import Constants, ConfigFileReader
import datetime

class JSDatasetGenerator(object):
    '''
    Created on 17 Apr 2012

    @author: rob
    '''
    # Field position in the dataList
    DATETIME_FIELD = 0
    RX_MIB_FIELD = 1
    TX_MIB_FIELD = 2
    RX_PERC_FIELD = 3
    TX_PERC_FIELD = 4
    
    def __init__(self):
        '''
        Constructor
        '''
        self._dataParser = None
        self._jsDataFile = None
        configFileReader = ConfigFileReader()
        self._jsFilePath = configFileReader.read(Constants.SEC_MAIN,
                                                 Constants.OPT_INSTALL_FOLDER)
        self._jsFilePath += Constants.JS_DATA_FILE_REL_PATH
        
    # *************************************************************************
    def setDataParser(self, dataParser):
        self._dataParser = dataParser
        
    # *************************************************************************
    def generateUpdateTimeRecord(self):
        '''
        Generates an entry in the Javascript data set to identify the last time
        the vnstat data were updated.
        '''
        dateutc = self._dataParser.parseUpdateTime()
        if (dateutc != 0):
            dateutc = datetime.datetime.utcfromtimestamp(dateutc)
        else:
            dateutc = "Not readable"
        
        self._openJSDataFile()
        self._openJSDataObject(Constants.UPDATE_TIME_DATASET_NAME)
        self._jsDataFile.write("\n\tdata: \"")
        self._jsDataFile.write(str(dateutc))
        self._jsDataFile.write("\"\n")
        self._closeJSDataObject()
        
        
    
    # *************************************************************************
    def generateHourlyDataSet(self):
        dataList = self._dataParser.parseHourlyData()
        dataSet = self._generateChartData(dataList, self._buildBarChartTimeref)
        # Let's write results to file
        self._writeBarChartJSObject(Constants.HOURS_CHART_DATASET_NAME,
                                    dataSet)
    
    # *************************************************************************
    def generateDailyDataSet(self):
        dataList = self._dataParser.parseDailyData()
        dataSet = self._generateChartData(dataList, self._buildLineChartTimeref)
        # Let's write results to file
        self._writeLineChartJSDataObject(Constants.DAYS_CHART_DATASET_NAME,
                                         dataSet)
    
    # *************************************************************************
    def generateMonthlyDataSet(self):
        dataList = self._dataParser.parseMonthlyData()
        dataSet = self._generateSmallMultiplesData(dataList)
        
        self._writeSmallMultiplesJSDataObject(Constants.MONTHS_CHART_DATASET_NAME,
                                         dataSet)
        # For testing the method
        return dataSet
    
    # *************************************************************************
    def generateTopTenDaysDataSet(self):
        dataList = self._dataParser.parseTopTenDaysData()
        dataSet = self._generateChartData(dataList, self._buildLineChartTimeref)
        
        self._writeTopTenChartJSObject(Constants.TOP_TEN_DAYS_DATASET_NAME,
                                       dataSet)
    # *************************************************************************
    def cleanup(self):
        self._closeJSDataFile()
        
    # *************************************************************************
    def _buildBarChartTimeref(self, dateutc):
        # We are only interested in the hours
        return dateutc.hour
    
    # *************************************************************************
    def _buildLineChartTimeref(self, dateutc):
        timeref = "Date.UTC(" + str(dateutc.year) + ","
        # Months are one based but we want them zero based
        timeref = timeref + str(dateutc.month - 1) + ","
        timeref = timeref + str(dateutc.day) + ","
        timeref = timeref + str(dateutc.hour) + ","
        timeref = timeref + str(dateutc.minute) + ","
        timeref = timeref + str(dateutc.second) + ")"
        
        return timeref
    
    # *************************************************************************
    def _generateChartData(self, dataList, timerefFunc):
        self._openJSDataFile()
        
        arrTimeRef = []
        arrRxMiB = []
        arrTxMiB = []
        rxMiB = ""
        txMiB = ""
        
        for data in dataList:
            dateutc = datetime.datetime.utcfromtimestamp(float(data[JSDatasetGenerator.DATETIME_FIELD]))
            # We add one hour because vnstat is measuring traffic at min 59
            # leading to a wrong day indication on the chart in some cases.
            dateutc += datetime.timedelta(hours = 1)
            # Calling the pointed function passing the date object
            timeref = timerefFunc(dateutc)
            # Rounding down to two decimal places value calculated for MiBs
            rxMiB = str(round(data[JSDatasetGenerator.RX_MIB_FIELD], 2))
            txMiB = str(round(data[JSDatasetGenerator.TX_MIB_FIELD], 2))
            
            arrTimeRef.append(timeref)
            arrRxMiB.append(rxMiB)
            arrTxMiB.append(txMiB)
        
        return [arrTimeRef, arrRxMiB, arrTxMiB]
    
    # *************************************************************************
    # To calculate percentages:
    #
    #    - Find the maxValue element of the month looking in both Tx and Rx
    #     (the min will be zero). The maxValue will represent the 100%
    #      and all the others will be calculated and drawn in respect to
    #      this value (they will be a percentage of that)
    #
    #   - For each line (entry) generate an entry for the chart calculating:
    #       - the percentage for the representative point (the top at the center)
    #       - the percentages for the other points in relation to the ratio
    #           those other points have with the top one
    #   
    #   - Write the entry that the chart will consume, representing a SM tail
    #   
    #   
    #    Example of the data set:
    #   
    #    [ [ DateUTC(YYY, MM, DD), [Rx %] , [Tx %] ], 
    #      [ DateUTC(YYY, MM, DD), [Rx %] , [Tx %] ], ...]
    #
    #    To create the desired shape this are the proportions:
    #
    #        [0, 50, 30, 100, 30, 50, 0 ]
    #
    #    where the 100 represent the central point to calculate while the
    #    others need be calculated in respect of the 100 percent, and have to be
    #    30%, 50% etc from the central value.
    #
    #    See testing class for what is expected.
    #
    def _generateSmallMultiplesData(self, dataList):
        #dataSet = []
        
        # This ratios will determine the shape of the chart
        percentRatios = [0, 50, 30, 100, 30, 50, 0]
        
        # Let's find the maxValue in both rx and tx entries
        maxValue = 0
        for entry in dataList:
            entryMax = entry[JSDatasetGenerator.RX_MIB_FIELD]
            if (entry[JSDatasetGenerator.RX_MIB_FIELD] < entry[JSDatasetGenerator.TX_MIB_FIELD]):
                entryMax = entry[JSDatasetGenerator.TX_MIB_FIELD]
                
            if (entryMax > maxValue):
                maxValue = entryMax
        #print(str(maxValue))
        arrTimeRef = []
        arrRxMiB = []
        arrTxMiB = []
        arrRxPerc = []
        arrTxPerc = []
        # Let's create the dataset calculating the value with respect to the maxValue
        for entry in dataList:
            rxDataPerc = []
            txDataPerc = []
            dateutc = datetime.datetime.utcfromtimestamp(float(entry[JSDatasetGenerator.DATETIME_FIELD]))
            # We add one hour because vnstat is measuring traffic at min 59
            # leading to a wrong day indication on the chart in some cases.
            dateutc += datetime.timedelta(hours = 1)
            # Calling the pointed function passing the date object
            timeref = self._buildLineChartTimeref(dateutc)
            
            # Appending traffic data in MiB
            arrRxMiB.append(str(round(entry[JSDatasetGenerator.RX_MIB_FIELD], 2)))
            arrTxMiB.append(str(round(entry[JSDatasetGenerator.TX_MIB_FIELD], 2)))
            
            # Calculating percentages
            percRxVariation = (entry[JSDatasetGenerator.RX_MIB_FIELD] / maxValue) * 100
            percTxVariation = (entry[JSDatasetGenerator.TX_MIB_FIELD] / maxValue) * 100
            for ratio in percentRatios:
                rxDataPerc.append(str(round(ratio * percRxVariation / 100, 2)))
                txDataPerc.append(str(round(ratio * percTxVariation / 100, 2)))
            
            arrTimeRef.append(timeref)
            # I am converting to string because the array would be passed by
            # reference and not by value...
            arrRxPerc.append(str(rxDataPerc))
            arrTxPerc.append(str(txDataPerc))
            
        return [arrTimeRef, arrRxMiB, arrTxMiB, arrRxPerc, arrTxPerc]
    
    # *************************************************************************
    # 
    def _writeBarChartJSObject(self, chartDatasetName, dataSet):
        self._openJSDataFile()
        self._openJSDataObject(chartDatasetName)
        
        self._writeCategoriesDataObject(dataSet[JSDatasetGenerator.DATETIME_FIELD])
        self._writeSeriesDataObject(dataSet[JSDatasetGenerator.RX_MIB_FIELD],
                                    "\t\tmarker: { symbol: 'square' },\n",
                                    dataSet[JSDatasetGenerator.TX_MIB_FIELD],
                                    "\t\tmarker: { symbol: 'diamond' },\n")
            
        self._closeJSDataObject()
    
    # *************************************************************************
    def _writeLineChartJSDataObject(self, chartDatasetName, dataSet):
        self._openJSDataFile()
        self._openJSDataObject(chartDatasetName)
        
        arrSeriesRx = []
        arrSeriesTx = []
        #
        # We have the data set as a multidimensional array that can be thought
        # as being a table like:
        #
        #    DATETIME    RX_MIB    TX_MIB
        #    1234        123.44    53.33
        #
        # In the case of the small multiples the RX_MIB and TX_MIB
        # are array of percentages themselves.
        #
        # We use the DATETIME_FIELD to loop the rows but any of the three would do
        #
        for row in range(len(dataSet[JSDatasetGenerator.DATETIME_FIELD])):
            arrSeriesRx.append([dataSet[JSDatasetGenerator.DATETIME_FIELD][row],
                                dataSet[JSDatasetGenerator.RX_MIB_FIELD][row]])
            arrSeriesTx.append([dataSet[JSDatasetGenerator.DATETIME_FIELD][row],
                                dataSet[JSDatasetGenerator.TX_MIB_FIELD][row]])
                
        self._writeSeriesDataObject(arrSeriesRx,
                                    "\t\tmarker: { symbol: 'square' },\n",
                                    arrSeriesTx,
                                    "\t\tmarker: { symbol: 'diamond' },\n")
        
        self._closeJSDataObject()
    
    # *************************************************************************
    def _writeSmallMultiplesJSDataObject(self, chartDatasetName, dataSet):
        self._openJSDataFile()
        self._openJSDataObject(chartDatasetName)
        
        # Dataset fields received:
        #     arrTimeRef, arrRxMiB, arrTxMiB, arrRxPerc, arrTxPerc
        
        arrSeriesRx = []
        arrSeriesTx = []
        #
        # We have the data set as a multidimensional array that can be thought
        # as being a table like:
        #
        #    DATETIME    RX_MIB    TX_MIB    RX_PERC        TX_PERC
        #    1234        123.44    53.33     [0,35,50,..]   [0,12,20,...]
        #
        # In the case of the small multiples the RX_MIB and TX_MIB
        # are array of percentages themselves.
        #
        # We use the DATETIME_FIELD to loop the rows but any of the three would do
        #
        for row in range(len(dataSet[JSDatasetGenerator.DATETIME_FIELD])):
            arrSeriesRx.append([dataSet[JSDatasetGenerator.DATETIME_FIELD][row],
                                dataSet[JSDatasetGenerator.RX_PERC_FIELD][row]])
            arrSeriesTx.append([dataSet[JSDatasetGenerator.DATETIME_FIELD][row],
                                dataSet[JSDatasetGenerator.TX_PERC_FIELD][row]])
                
        self._writeSmallMultiplesSeriesDataObject(dataSet[JSDatasetGenerator.RX_MIB_FIELD],
                                                  dataSet[JSDatasetGenerator.TX_MIB_FIELD],
                                                  arrSeriesRx, arrSeriesTx,)
        
        self._closeJSDataObject()
    
    # *************************************************************************
    # 
    def _writeTopTenChartJSObject(self, chartDatasetName, dataSet):
        self._openJSDataFile()
        self._openJSDataObject(chartDatasetName)
        
        arrSeriesRx = []
        arrSeriesTx = []
        for row in range(len(dataSet[JSDatasetGenerator.DATETIME_FIELD])):
            arrSeriesRx.append([dataSet[JSDatasetGenerator.DATETIME_FIELD][row],
                                dataSet[JSDatasetGenerator.RX_MIB_FIELD][row]])
            arrSeriesTx.append([dataSet[JSDatasetGenerator.DATETIME_FIELD][row],
                                dataSet[JSDatasetGenerator.TX_MIB_FIELD][row]])
            
        self._writeSeriesDataObject(arrSeriesRx,
                                    "\t\tcolor: 'rgba(223, 83, 83, .5)',\n",
                                    arrSeriesTx,
                                    "\t\tcolor: 'rgba(119, 152, 191, .5)',\n")
            
        self._closeJSDataObject()
        
    # *************************************************************************
    # Writes the opening of a Javascript literal using the chartDatasetName
    # as the name of the literal.
    #
    def _openJSDataObject(self, chartDatasetName):
        self._jsDataFile.write("RODU.av4vnstat.data.")
        self._jsDataFile.write(chartDatasetName)
        self._jsDataFile.write(" = {\n")

    # *************************************************************************
    # Generates the Javascript data set expected by the linear chart type.
    # 
    def _writeSeriesDataObject(self, arrRxMiB, rxAttrs, arrTxMiB, txAttrs):
        # Opening the series filed
        self._jsDataFile.write("\tseries: [{\n")
        # Download
        self._jsDataFile.write("\t\tname: 'Download',\n")
        self._jsDataFile.write(rxAttrs)
        self._jsDataFile.write("\t\tdata: ")
        self._jsDataFile.write(str(arrRxMiB).replace("'", "").replace("\"", ""))
        self._jsDataFile.write("\n\t},{\n")
        # Upload
        self._jsDataFile.write("\t\tname: 'Upload',\n")
        self._jsDataFile.write(txAttrs)
        self._jsDataFile.write("\t\tdata: ")
        self._jsDataFile.write(str(arrTxMiB).replace("'", "").replace("\"", ""))
        self._jsDataFile.write("\n\t}]\n")
    
    # *************************************************************************
    # Generates the Javascript data set expected by the linear chart type.
    # 
    def _writeSmallMultiplesSeriesDataObject(self, arrRxMiB, arrTxMiB, arrRxPerc, arrTxPerc):
        # Opening the series filed
        self._jsDataFile.write("\tseries: [{\n")
        # Download
        self._jsDataFile.write("\t\tname: '',\n")
        self._jsDataFile.write("\t\ttraffic: ")
        self._jsDataFile.write(str(arrRxMiB).replace("'", "").replace("\"", ""))
        self._jsDataFile.write(",\n\t\tdata: ")
        self._jsDataFile.write(str(arrRxPerc).replace("'", "").replace("\"", ""))
        self._jsDataFile.write("\n\t},{\n")
        # Upload
        self._jsDataFile.write("\t\tname: '',\n")
        self._jsDataFile.write("\t\ttraffic: ")
        self._jsDataFile.write(str(arrTxMiB).replace("'", "").replace("\"", ""))
        self._jsDataFile.write(",\n\t\tdata: ")
        self._jsDataFile.write(str(arrTxPerc).replace("'", "").replace("\"", ""))
        self._jsDataFile.write("\n\t}]\n")
        
    # *************************************************************************
    # For testing pourposes we want to be able to set this from outside
    #
    def setJSFilePath(self, jsFilePath):
        self._jsFilePath = jsFilePath
        
    # *************************************************************************
    # Generates the Javascript data set expected by the bar chart type.
    # 
    def _writeCategoriesDataObject(self, arrTimeRef):
        self._jsDataFile.write("\n\tcategories: ")
        self._jsDataFile.write(str(arrTimeRef))
        self._jsDataFile.write(",\n")
    
    # *************************************************************************
    # Writes the closing of a Javascript literal
    #
    def _closeJSDataObject(self):
        self._jsDataFile.write("\n};\n")

    # *************************************************************************
    def _openJSDataFile(self):
        if (self._jsDataFile == None):
            try:
                self._jsDataFile = open(self._jsFilePath, 'w')
            except(IOError):
                print "Wrong configuration parameters!"
                print "\nCheck the 'install_folder' value given in the av4vnstat.cfg."
                print "The 'install_folder' must match the root folder containing the program."
                print "Execution terminated."
                exit(1)
    
    # *************************************************************************
    def _closeJSDataFile(self):
        if (not self._jsDataFile == None):
            self._jsDataFile.close()
    
