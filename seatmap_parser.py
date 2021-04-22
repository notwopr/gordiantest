'''
Author: David Choi
Date Started: 4.21.2021
Purpose: Parses seatmap information contained in an XML file and converts it into JSON format.

JSON OUTPUT DICT GLOSSARY:
'DepartureDate' is the date of the flight.
'DepartureTime' is the time of the flight.
'FlightNumber' is the flight number.
'DepartureAirport' is the airport code of the departure airport.
'ArrivalAirport' is the airport code of the arrival airport.
'AirplaneModel' is the model of the plane being flown for that flight.
'SeatNumber' is the seat number (1A, 2E, etc)
'SeatClass' is whether First Class, Economy, etc.
'SeatType' is whether it is an aisle, window or middle seat.
'ExitSeat' is true or false and whether it is a seat in a row where the plane exits are located.
'SeatPrice' is the base price of the seat.
'SeatPriceCurrency' is the currency of the SeatPrice.
'SeatTax' is the tax of the seat.
'SeatTaxCurrency' is the currency of the SeatTax.
'SeatAvail' is true or false, whether it is available to purchase or not.
'''
# IMPORT TOOLS
#   STANDARD LIBRARY IMPORTS
import sys
import xml.etree.ElementTree as ET
import json
import datetime as dt
#   THIRD PARTY IMPORTS
#   LOCAL APPLICATION IMPORTS


def cleanbranchtag(rawbranch):
    tagtext = rawbranch
    addy1 = '{http://schemas.xmlsoap.org/soap/envelope/}'
    addy2 = '{http://www.opentravel.org/OTA/2003/05/common/}'
    addy3 = '{http://www.iata.org/IATA/EDIST/2017.2}'
    tagtext = tagtext.replace(addy1, '')
    tagtext = tagtext.replace(addy2, '')
    tagtext = tagtext.replace(addy3, '')
    return tagtext


# update seat-specific dict with price info
def OTAv1_addpricing(keyname, branchdict, seatval):
    # get amount
    amount = branchdict["Amount"]
    # add decimal if applies and convert to float
    if 'DecimalPlaces' in branchdict.keys():
        decimalplaces = int(branchdict["DecimalPlaces"])
        insertchar = '.'
        amount = amount[:-decimalplaces] + insertchar + amount[-decimalplaces:]
        amount = float(amount)
    else:
        amount = float(amount)
    # add amount to seat-specific dict
    seatval.update({f'Seat{keyname}': amount})
    # add currency type if available
    if 'CurrencyCode' in branchdict.keys():
        currencycode = branchdict["CurrencyCode"]
        seatval.update({f'Seat{keyname}Currency': currencycode})
    return seatval


# seatmap parser for OTA_AirSeatMapRS Version 1 XML files
def jsonseatmapparser_OTAv1(jsonseatmapdata, root, rowcurr, seatnumber, seatval):
    # for each branch in xml file,
    for branch in root.iter():
        if branch.attrib is not None:
            if len(branch.attrib) != 0:
                # add flight info
                if 'DepartureDateTime' in branch.attrib.keys():
                    datetimestr = branch.attrib['DepartureDateTime']
                    # parse flight date and time
                    departdtobj = dt.datetime.strptime(datetimestr, '%Y-%m-%dT%H:%M:%S')
                    depdate = departdtobj.strftime("%Y-%m-%d")
                    deptime = departdtobj.strftime("%H:%M:%S")
                    # add flight date and time to output dict
                    jsonseatmapdata['FlightInfo'].update({
                        'DepartureDate': depdate,
                        'DepartureTime': deptime,
                        })
                # add flight number
                if 'FlightNumber' in branch.attrib.keys():
                    # add flight number to output dict
                    jsonseatmapdata['FlightInfo'].update({
                        'FlightNumber': branch.attrib['FlightNumber']
                        })
                # add airport codes
                if 'LocationCode' in branch.attrib.keys():
                    # determine whether departing or arrival airport code
                    if branch.tag is not None and len(branch.tag) != 0:
                        tagtext = cleanbranchtag(branch.tag)
                        if tagtext == 'DepartureAirport':
                            keyname = 'DepartureAirport'
                        elif tagtext == 'ArrivalAirport':
                            keyname = 'ArrivalAirport'
                        # add flight number to output dict
                        jsonseatmapdata['FlightInfo'].update({
                            keyname: branch.attrib['LocationCode']
                            })
                # add airplane model
                if 'AirEquipType' in branch.attrib.keys():
                    # add airplane model to output dict
                    jsonseatmapdata['FlightInfo'].update({
                        'AirplaneModel': branch.attrib['AirEquipType']
                        })
                # add seatrow and set current row
                if 'RowNumber' in branch.attrib.keys():
                    # update row dict with seat-specific data present if present
                    if seatnumber != '' and len(seatval) != 0:
                        jsonseatmapdata['SeatMap'][f'Row{rowcurr}'].update({seatnumber: seatval})
                        # clear seat-specific dict
                        seatval = {}
                        # clear seat number
                        seatnumber = ''
                    # set current row number
                    rowcurr = branch.attrib["RowNumber"]
                    # add row key to output dict
                    jsonseatmapdata['SeatMap'].update({f'Row{rowcurr}': {}})
                    # set current seat class
                    if 'CabinType' in branch.attrib.keys():
                        classcurr = branch.attrib["CabinType"]
                # set whether seat is in an exit row
                if 'ExitRowInd' in branch.attrib.keys():
                    isexitrow = branch.attrib["ExitRowInd"]
                # set current seat number
                if 'SeatNumber' in branch.attrib.keys():
                    # update row dict with seat-specific data present if present
                    if seatnumber != '' and len(seatval) != 0:
                        jsonseatmapdata['SeatMap'][f'Row{rowcurr}'].update({seatnumber: seatval})
                        # clear seat-specific dict
                        seatval = {}
                    seatnumber = branch.attrib["SeatNumber"]
                    # add to seat-specific dict
                    seatval.update({'SeatNumber': seatnumber, 'SeatClass': classcurr, 'ExitSeat': isexitrow})
                # set seat price and tax
                if 'Amount' in branch.attrib.keys():
                    # determine whether amount is base price or tax
                    if branch.tag is not None and len(branch.tag) != 0:
                        tagtext = cleanbranchtag(branch.tag)
                        if tagtext == 'Fee':
                            keyname = 'Price'
                        elif tagtext == 'Taxes':
                            keyname = 'Tax'
                        # add price info to seat-specific dict
                        seatval = OTAv1_addpricing(keyname, branch.attrib, seatval)
                # set seat availability
                if 'AvailableInd' in branch.attrib.keys():
                    if branch.attrib["AvailableInd"] == 'false':
                        seatavail = 'no'
                    elif branch.attrib["AvailableInd"] == 'true':
                        seatavail = 'yes'
                    # add to seat-specific dict
                    seatval.update({'SeatAvail': seatavail})
        # set whether seat is window, aisle, or center
        if branch.text is not None:
            if len(branch.text) != 0 and branch.text.isspace() is False:
                if branch.text.rstrip() in ['Window', 'Aisle', 'Center']:
                    seattypecurr = branch.text
                    # add to seat-specific dict
                    seatval.update({'SeatType': seattypecurr})
    return jsonseatmapdata


# convert seat definition elements into dict
def getpricedefinitions(branch):
    pricedefdict = {}
    # for each alacartoffer type
    for element in branch:
        elemtagtext = cleanbranchtag(element.tag)
        if elemtagtext == 'ALaCarteOfferItem':
            # get offer id
            priceID = element.get('OfferItemID')
            pricedefdict.update({priceID: {}})
            for subelem in element.iter():
                subeltag = cleanbranchtag(subelem.tag)
                if subeltag == 'SimpleCurrencyPrice':
                    # get currencycode
                    currencycode = subelem.get('Code')
                    # get price
                    price = subelem.text
            pricedefdict[priceID].update({'Price': price, 'CurrencyCode': currencycode})
    return pricedefdict


# convert seat definition elements into dict
def getseatdefinitions(branch):
    seatdefdict = {}
    for element in branch:
        seatdefID = element.get('SeatDefinitionID')
        # set custom idtext if necessary
        if seatdefID == 'SD3':
            idtext = 'Window'
        elif seatdefID == 'SD5':
            idtext = 'Aisle'
        else:
            idtext = element[0][0].text
        seatdefdict.update({seatdefID: idtext})
    return seatdefdict


# seatmap parser for OTA_AirSeatMapRS Version 1 XML files
def jsonseatmapparser_IATA(jsonseatmapdata, root, rowcurr, seatnumber, seatval):
    # set pricing definitionlist
    for branch in root.iter():
        tagtext = cleanbranchtag(branch.tag)
        if tagtext == 'ALaCarteOffer':
            pricedefdict = getpricedefinitions(branch)
    # create seatdefinitionlist
    for branch in root.iter():
        tagtext = cleanbranchtag(branch.tag)
        # set seat definition dict
        if tagtext == 'SeatDefinitionList':
            seatdefdict = getseatdefinitions(branch)
    for branch in root.iter():
        if branch.tag is not None and len(branch.tag) != 0:
            tagtext = cleanbranchtag(branch.tag)
            # set current row
            if tagtext == 'Row':
                for child in branch:
                    subtagtext = cleanbranchtag(child.tag)
                    if subtagtext == 'Number':
                        rowcurr = child.text
                        # add row key to output dict
                        jsonseatmapdata['SeatMap'].update({f'Row{rowcurr}': {}})
                    # set seat-specific info
                    if subtagtext == 'Seat':
                        seatdeflist = []
                        for seatelem in child:
                            seattagtext = cleanbranchtag(seatelem.tag)
                            if seattagtext == 'Column':
                                colcurr = seatelem.text
                                seatnumber = f'{rowcurr}{colcurr}'
                                jsonseatmapdata['SeatMap'][f'Row{rowcurr}'].update({seatnumber: {}})
                                # set seatnumber
                                jsonseatmapdata['SeatMap'][f'Row{rowcurr}'][seatnumber].update({'SeatNumber': seatnumber})
                            # set pricing info
                            if seattagtext == 'OfferItemRefs':
                                seatprice = pricedefdict[seatelem.text]['Price']
                                seatpricecurrency = pricedefdict[seatelem.text]['CurrencyCode']
                                jsonseatmapdata['SeatMap'][f'Row{rowcurr}'][seatnumber].update({'SeatPrice': seatprice, 'SeatPriceCurrency': seatpricecurrency})
                            if seattagtext == 'SeatDefinitionRef':
                                seatdeflist.append(seatelem.text)
                                # set seattype
                                if seatelem.text in ['SD3', 'SD5']:
                                    jsonseatmapdata['SeatMap'][f'Row{rowcurr}'][seatnumber].update({'SeatType': seatdefdict[seatelem.text]})

                        # set center seat type
                        if 'SD3' not in seatdeflist and 'SD5' not in seatdeflist:
                            jsonseatmapdata['SeatMap'][f'Row{rowcurr}'][seatnumber].update({'SeatType': 'Center'})
                        # set seat availability
                        if 'SD4' in seatdeflist:
                            seatavail = 'yes'
                        else:
                            seatavail = 'no'
                        jsonseatmapdata['SeatMap'][f'Row{rowcurr}'][seatnumber].update({'SeatAvail': seatavail})
                        # seat whether exit seat
                        if 'SD14' in seatdeflist:
                            isexitseat = 'true'
                        else:
                            isexitseat = 'false'
                        jsonseatmapdata['SeatMap'][f'Row{rowcurr}'][seatnumber].update({'ExitSeat': isexitseat})

            # set departure info
            if tagtext == 'Departure':
                for sub_branch in branch:
                    subtagtext = cleanbranchtag(sub_branch.tag)
                    # set departure airport code
                    if subtagtext == 'AirportCode':
                        jsonseatmapdata['FlightInfo'].update({'DepartureAirport': sub_branch.text})
                    # set departure date
                    if subtagtext == 'Date':
                        jsonseatmapdata['FlightInfo'].update({'DepartureDate': sub_branch.text})
                    # set departure time
                    if subtagtext == 'Time':
                        jsonseatmapdata['FlightInfo'].update({'DepartureTime': sub_branch.text})
            # set arrival airport code
            if tagtext == 'Arrival':
                for sub_branch in branch:
                    subtagtext = cleanbranchtag(sub_branch.tag)
                    # set departure airport code
                    if subtagtext == 'AirportCode':
                        jsonseatmapdata['FlightInfo'].update({'ArrivalAirport': sub_branch.text})
            # set carrier
            if tagtext == 'AirlineID':
                jsonseatmapdata['FlightInfo'].update({'Carrier': branch.text})
            # set flight number
            if tagtext == 'FlightNumber':
                # add airport code to output dict
                jsonseatmapdata['FlightInfo'].update({'FlightNumber': branch.text})
            # set airplane model
            if tagtext == 'AircraftCode':
                # add airport code to output dict
                jsonseatmapdata['FlightInfo'].update({'AirplaneModel': branch.text})
    return jsonseatmapdata


if __name__ == "__main__":
    '''OPEN XML FILE'''
    # get inputfilename
    inputfilename = sys.argv[1]
    # exit script if input file is not in XML format
    if inputfilename.lower().endswith('.xml') is False:
        print(f'The input file {inputfilename} is not in XML format.  Parser script is now exiting...')
        exit()
    else:
        # establish output dict object
        jsonseatmapdata = {
            'FlightInfo': {},
            'SeatMap': {}
            }
        # open input file
        tree = ET.parse(inputfilename)
        root = tree.getroot()
        # set super-branch level var values
        rowcurr = ''
        classcurr = ''
        seatnumber = ''
        seatval = {}
        # run xml parser
        if inputfilename.lower() == 'seatmap1.xml':
            jsonseatmapdata = jsonseatmapparser_OTAv1(jsonseatmapdata, root, rowcurr, seatnumber, seatval)
        elif inputfilename.lower() == 'seatmap2.xml':
            jsonseatmapdata = jsonseatmapparser_IATA(jsonseatmapdata, root, rowcurr, seatnumber, seatval)
        '''SAVE CONTENTS TO JSON FILE'''
        # define outputfilename
        outputfilename = f'{inputfilename[:-4]}_parsed.json'
        # save final dict data to file
        with open(outputfilename, 'w') as outputfile:
            json.dump(jsonseatmapdata, outputfile)
        # optional verbose printing
        print(f'The input file {inputfilename} was converted and saved to {outputfilename}.  Parser script is now exiting...')
