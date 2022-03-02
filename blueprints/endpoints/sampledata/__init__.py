from flask import request
from flask_restx import Namespace, Resource, fields
from pathlib import Path
import json
from datetime import datetime
import time
import pandas as pd
import os
import requests
from blueprints.endpoints.plotlydash.html_functions import get_file_contents_and_analyze

# creates the /sampledata enpoint
namespace = Namespace('sampledata', 'Endpoint for gilson to post its data.')

#A model of what the json file will look like that gets posted to the endpoint
sampledata_model = namespace.model('sampledata_model', {
    "sampleData":fields.Nested(namespace.model('sampleData', {
        "systemName":fields.String,
        "machineId":fields.String,
        "resultId":fields.String,
        "name":fields.String,
        "createdBy":fields.String,
        "description":fields.String,
        "runData":fields.List(fields.Nested(namespace.model('runData', {
            "runDate":fields.String,
            "reportDate":fields.String,
            "sampleListName":fields.String,
            "sampleListID":fields.String,
            "sampleStep":fields.String,
            "methodName":fields.String,
            "imageFormat":fields.String,
            "imageEncoding":fields.String,
            "runImage":fields.String,
            "fractionCollectionType":fields.String,
            "fractionFrontSlope":fields.String,
            "fractionBackSlope":fields.String,
            "fractionPeakWidth":fields.String,
            "fractionPeakBaseLevel":fields.String,
            "fractionPeakLevel":fields.String,
            "fractionPeakLevelUnits":fields.String,
            "fractionPeakLevelOperation":fields.String,
            "fractionPart":fields.String,
            "fractionSeperateCo-elutedPeaks":fields.String,
            "fractionCollectPositivePeaks":fields.String,
            "fractionCollectNegativePeaks":fields.String,
            "fractionCollectPeakCollectionType":fields.String,
            "fractionCollectPeakTimePerTube":fields.String,
            "fractionCollectPeakVolumePerTube":fields.String,
            "fractionCollectNonPeaks":fields.String,
            "fractionCollectNonPeakCollectionType":fields.String,
            "fractionCollectNonPeakTimePerTube":fields.String,
            "fractionCollectNonPeakVolumePerTube":fields.String,
            "fractionTimeUnits":fields.String,
            "fractionVolumeUnits":fields.String,
            "#SAMPLE WELL":fields.String,
            "#SAMPLE ZONE":fields.String,
            "#FRACTION WELL":fields.String,
            "#FRACTION ZONE":fields.String,
            "#INJECTION WELL":fields.String,
            "#INJECTION ZONE":fields.String,
            "#INJECTION VOLUME":fields.String,
            "#FLOW RATE":fields.String
        }))),
        "resultNotifications":fields.Nested(namespace.model('resultNotifications', {
            "notifications":fields.Nested(namespace.model('notifications', {
                "Notify_MehtodCompletion at YYYY-MM-DDThh:mm:ss.fff":fields.String
            }))
        })),
        "analysisData":fields.List(fields.Nested(namespace.model('analysisData', {
            "analysisName":fields.String,
            "metadata":fields.Nested(namespace.model('metadata2', {
                "peakTimeUnits":fields.String
            })),
            "etc...":fields.Float
        }))),
        "pressures": fields.List(fields.Nested(namespace.model('pressures', {
            "pressureData":fields.Nested(namespace.model('pressureData', {
                "data":fields.List(fields.Nested(namespace.model('datap', {
                    "X":fields.Float,
                    "Y":fields.Float
                })))
            }))
        })))
    }))
})

def check_error_log_size():
    '''Deletes error_log.txt if it is bigger than 10,000 bytes'''
    error_log_path = Path('.//reference_files//error_log.txt')
    size = os.path.getsize(error_log_path.absolute()) 
    if size > 10000:
        f = open(error_log_path.absolute(),"w")
        f.close()

def append_error_log(error, fatal):
    '''Checks log size, finds, sourceplate, adds error to log, skips if fatal'''
    check_error_log_size()

    samplelist_path = Path('.//reference_files//samplelist.json')
    with open(samplelist_path.absolute(), 'r') as f:
        samplelist = json.load(f)
        sourceplate = samplelist["sampleLists"][0]["description"]
        f.close()

    error_log_path = Path('.//reference_files//error_log.txt')
    with open(error_log_path.absolute(), 'r') as f:
        current_error_log = f.read()
        f.close()

    with open(error_log_path.absolute(), 'w') as f:
        f.write(str(current_error_log) + str(datetime.fromtimestamp(time.time()).ctime()) + "|" + sourceplate +  ": " + error + "\n\n")
        f.close()

    if fatal:
        requests.post('http://localhost:5000/gilson_REST/webfront/skip_all', '')

@namespace.route('')
class sampledata(Resource):
    '''A place to post JSON data from gilson'''

    # provides a place for gilson to POST its data and can change the response
    @namespace.response(500, 'Internal Server Error.')
    @namespace.response(204, 'Request success (no content)')
    @namespace.expect(sampledata_model)
    def post(self):
        '''
        Gets data, checks if Standard and Pressures are okay, puts data into database, and sends Gilson the next method to run. 
        TO TEST: Put the current method name and sample list ID in the 'methodName' and 'sampleListID' objects post. Put 'Gilson_#' in 'systemName'.
        '''

        # Pass / no pass variable
        success = True 

        # Get Samplelist ID, method name, pressures, and system name
        sampleListId = request.json["sampleData"]["runData"][0]["sampleListID"]
        methodName = request.json["sampleData"]["runData"][0]["methodName"]
        pressures = request.json["sampleData"]["pressures"][0]["pressureData"]["data"]
        hostname = request.json["sampleData"]["systemName"]

        # Creating the filepath from the hostname
        parent_dir = ".//reference_files//" + hostname

        # Pressure check TODO: Put Better Pressure Check
        for pressure in pressures:
            if pressure["Y"] > 700:
                append_error_log("-ERROR- Pressure of " + pressure["Y"] + " too high.", fatal=True)
                success = False

        # Standard Check
        if "STD" in methodName:

            # dumping STD into most_recent_standard.json
            most_recent_std_path = Path(parent_dir + "//most_recent_standard.json")
            with open(most_recent_std_path.absolute(), 'w') as f:
                json.dump(request.json, f)
                f.close()
            
            # Getting thresholds from config file
            config_path = Path(parent_dir + "//config.json")
            with open(config_path.absolute(), 'r') as f:
                config_json = json.load(f)
                threshold_position = config_json["STDPositionThreshold"]
                threshold_fwhm = config_json["STDFWHMThreshold"]
                threshold_height = config_json["STDHeightThreshold"]
                f.close()
            
            # data analysis
            ref_df = pd.read_csv(parent_dir + "//reference_std.csv")
            data_table, diff, fig, info_card, ref_df_filtered = get_file_contents_and_analyze(request.json, ref_df) # Sharuyas logic

            # If ref_df == diff than there was no peaks and the Standard was not put in
            comparison = diff == ref_df_filtered
            equal_arrays = comparison.all().all()
            if equal_arrays:
                append_error_log("No standard present. Check http://localhost:5000/standardapp/ for info.", fatal=True)
                success = False

            # checking if differences are within tolorance
            thresholds = [threshold_position, threshold_height, threshold_fwhm]
            for index, row in diff.iterrows():
                if index == 0 and success:
                    for i in range(len(row.index)):
                        if row[i] >= thresholds[index] or row[i] <= -thresholds[index]:
                            append_error_log("-ERROR- Standard Peak position off. Check http://localhost:5000/standardapp/ for info.", fatal=True)
                            success = False
                            break

                elif index == 1 and success:
                    for i in range(len(row.index)):
                        if row[i] >= thresholds[index] or row[i] <= -thresholds[index]:
                            append_error_log("-WARNING- height for " + diff.columns[i] + " not within threshold.", fatal=False)

                elif index == 2 and success:
                    for i in range(len(row.index)):
                        if row[i] >= thresholds[index] or row[i] <= -thresholds[index]:
                            append_error_log("-WARNING- FWHM for " + diff.columns[i] + " not within threshold.", fatal=False)

        
        # If checks pass, give the Gilson the next samplelist
        samplelistqueue_path = Path(parent_dir + "//samplelistqueue.json")
        with open(samplelistqueue_path.absolute(), 'r') as f:
            samplelist_queue = json.load(f)
            if success:
                # Finds the next method to place into samplelist
                current_method = False
                for i, method in enumerate(samplelist_queue["sampleLists"]):
                    if current_method == True:
                        if method["columns"][0]["SKIPPAUSE"] == "SKIP":
                            pass
                        else:
                            next_method = dict(method)
                            break

                    elif method["id"] == sampleListId:
                        current_method = True

                    if sampleListId == "Stop":
                        next_method = samplelist_queue["sampleLists"][-1]
                        break

                f.close()

            else:
                # Finds shutdown method
                next_method = samplelist_queue["sampleLists"][-1]
                f.close()

        # Put the next method into samplelist.json
        samplelist_path = Path(parent_dir + "//samplelist.json")
        with open(samplelist_path.absolute(), 'w') as f:
            json.dump({"sampleLists": [next_method]}, f)
            f.close()
        
        #TODO: Put the data into the database
        # requests.post("u/r/l", data=request.json)
        
        return 204 