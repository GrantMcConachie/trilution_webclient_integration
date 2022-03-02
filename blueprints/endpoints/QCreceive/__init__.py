from flask_restx import Namespace, Resource, fields
from flask import request
import requests
import json
from pathlib import Path
import time
from datetime import datetime

namespace = Namespace(
    "QCreceive",
    "Receives the sourceplate from Gilson.PlateChecker and creates list of samplelists and samplelist",
)

QCrecieve_example = namespace.model("QCreceive", {"sourceplate": fields.String, "hostname": fields.String})

@namespace.route("")
class qc_receive(Resource):
    """Place to POST source plate
    TO TEST: 'sourceplate' is the source plate number. 'hostname' is Gilson_#.
    """

    @namespace.response(500, "Internal Server Error.")
    @namespace.response(200, "success")
    @namespace.expect(QCrecieve_example)
    def post(self):
        """Endpoint for scanning Gilson software"""

        # Gets the gilson information
        hostname = request.json["hostname"].upper()
        parent_dir = ".//reference_files//" + hostname

        # Recive sourceplate info and GET from npsg worklist endpointsss
        source_plate = request.json["sourceplate"]        
        npsg_url = "path/to/NIH/database"
        vlan_npsg_url = "path/to/NIH/database"
        worklist_string = requests.get(
            vlan_npsg_url + source_plate
        ).text
        worklist = json.loads(worklist_string)

        # Access config.json to get configuration
        config_path = Path(parent_dir + "//config.json")
        with open(config_path.absolute(), 'r') as f:
            config = json.load(f)
            samplesInBetweenSTDsMax = config["samplesInBetweenSTDsMax"]
            samplesInBetweenSTDsMin = config["samplesInBetweenSTDsMin"]
            numberOfSampleLists = config["numberOfSampleLists"]
            samplelistHeader = config["samplelistHeader"]
            startupMethod = config["startupMethod"]
            flushMethod = config["flushMethod"]
            STDMethod = config["STDMethod"]
            subfractionMethod = config["subfractionMethod"]
            fillSourceplateMethod = config["fillSourceplateMethod"]
            shutdownMethod = config["shutdownMethod"]
            blankWorklist = config["blankWorklist"]
            f.close()

        # Finding best way to break up number of samples
        split_number = [i for i in range(samplesInBetweenSTDsMin, samplesInBetweenSTDsMax + 1) if len(worklist) % i == 0]
        if split_number == []:
            for i in range(samplesInBetweenSTDsMin, samplesInBetweenSTDsMax + 1):
                split_number.append(len(worklist) % i)
            
            max_modulus_index = split_number.index(max(split_number))
            split_number = [samplesInBetweenSTDsMin + max_modulus_index]

        # Adding in blank wells if one of plates aren't filled all the way 2nd stage
        if source_plate[0:2] == "15" and len(worklist) % 4 != 0:
            for i in range(4 - (len(worklist) % 4)):
                last_well = float(worklist[-1]["FRACTION_WELL"])
                last_destionation_plate = worklist[-1]["DESTINATION_PLATE"]
                last_sample_plate = worklist[-1]["SAMPLE_PLATE"]
                blankWorklist["DESTIONATION_PLATE"] = last_destionation_plate
                blankWorklist["FRACTION_WELL"] = last_well + 22
                blankWorklist["SAMPLE_PLATE"] = last_sample_plate
                blankWorklist["STOP_FRCOL"] = 12.3
                blankWorklist["SAMPLE"] = "BLANK (fill last plate)"
                worklist.append(dict(blankWorklist))
        
        # Adding in blank wells if one of plates aren't filled all the way 3rd stage
        elif source_plate[0:2] == "16":
            # arithmatic to figure out where the plate left off
            last_subfraction = worklist[-1]
            number_of_wells = 2 * (float(last_subfraction["STOP_FRCOL"]) - float(last_subfraction["START_FRCO"]))
            ending_well = float(last_subfraction["FRACTION_WELL"]) + (number_of_wells - 1)
            ending_well_count = ending_well
            
            # Adding blank wells to plate to fill up the plate
            wells_needed = 0
            while ending_well_count % 88 != 0:
                wells_needed += 1
                ending_well_count += 1

            # If less than 22 wells are needed to fill up the plate
            if wells_needed > 0 and wells_needed <= 22:
                last_destionation_plate = worklist[-1]["DESTINATION_PLATE"]
                last_sample_plate = worklist[-1]["SAMPLE_PLATE"]
                blankWorklist["DESTINATION_PLATE"] = last_destionation_plate
                blankWorklist["FRACTION_WELL"] = ending_well + 1
                blankWorklist["SAMPLE_PLATE"] = last_sample_plate
                blankWorklist["STOP_FRCOL"] = 1.3 + (wells_needed / 2)
                blankWorklist["SAMPLE"] = "BLANK (fill last plate)"
                worklist.append(dict(blankWorklist))

            # If more than 22 wells are needed to fill up the plate
            elif wells_needed != 0 and wells_needed > 22:
                # Doing full subfraction methods until the plate is almost full
                for i in range(wells_needed//22):
                    last_destionation_plate = worklist[-1]["DESTINATION_PLATE"]
                    last_sample_plate = worklist[-1]["SAMPLE_PLATE"]
                    blankWorklist["DESTINATION_PLATE"] = last_destionation_plate
                    blankWorklist["FRACTION_WELL"] = ending_well + 1 + i * 22 
                    blankWorklist["SAMPLE_PLATE"] = last_sample_plate
                    blankWorklist["STOP_FRCOL"] = 12.3
                    blankWorklist["SAMPLE"] = "BLANK (fill last plate)"
                    worklist.append(dict(blankWorklist))

                # Finding which well to start on and how many wells to fill the final wells
                fraction_well = ending_well + 1 + (i + 1) * 22
                last_well_in_plate = fraction_well
                while last_well_in_plate % 88 != 0:
                    last_well_in_plate += 1

                stop_frcol = 1.3 + (last_well_in_plate - fraction_well + 1) / 2
                
                last_destionation_plate = worklist[-1]["DESTINATION_PLATE"]
                last_sample_plate = worklist[-1]["SAMPLE_PLATE"]
                blankWorklist["DESTINATION_PLATE"] = last_destionation_plate
                blankWorklist["FRACTION_WELL"] = fraction_well
                blankWorklist["SAMPLE_PLATE"] = last_sample_plate
                blankWorklist["STOP_FRCOL"] = stop_frcol
                blankWorklist["SAMPLE"] = "BLANK (fill last plate)"
                worklist.append(dict(blankWorklist))
            
            # If not an even number of plates add a blank plate
            if (ending_well//88) % 2 != 0:
                for i in range(4):
                    last_well = float(worklist[-1]["FRACTION_WELL"])
                    last_destionation_plate = worklist[-1]["DESTINATION_PLATE"]
                    last_sample_plate = worklist[-1]["SAMPLE_PLATE"]
                    blankWorklist["DESTIONATION_PLATE"] = last_destionation_plate
                    blankWorklist["FRACTION_WELL"] = 881 + i * 22
                    blankWorklist["SAMPLE_PLATE"] = last_sample_plate
                    blankWorklist["STOP_FRCOL"] = 12.25
                    blankWorklist["SAMPLE"] = "BLANK (for balance)"
                    worklist.append(dict(blankWorklist))

        # Create samplelist
        samplelistHeader["createDate"] = str(datetime.fromtimestamp(time.time()).isoformat())
        samplelistHeader["startDate"] = str(datetime.fromtimestamp(time.time()).isoformat())
        samplelistHeader["endDate"] = str(datetime.fromtimestamp(time.time()).isoformat())
        samplelistHeader["description"] = source_plate
        samplelistHeader["columns"] = [dict(startupMethod)]
        samplelistHeader["name"] = startupMethod["METHODNAME"]
        samplelistHeader["id"] = startupMethod["SAMPLENAME"]
        samplelist = {"sampleLists": [dict(samplelistHeader)]}

        blank = False
        for i, sample in enumerate(worklist):
            # Putting a standard and flush before blanks
            if "BLANK" in sample["SAMPLE"] and blank == False:
                samplelistHeader["columns"] = [dict(flushMethod)]
                samplelistHeader["name"] = flushMethod["METHODNAME"]
                samplelistHeader["id"] = flushMethod["SAMPLENAME"] + str(i)
                samplelist["sampleLists"].append(dict(samplelistHeader))

                samplelistHeader["columns"] = [dict(STDMethod)]
                samplelistHeader["name"] = STDMethod["METHODNAME"]
                samplelistHeader["id"] = STDMethod["SAMPLENAME"] + str(i)
                samplelist["sampleLists"].append(dict(samplelistHeader))
                blank = True

            # Splitting up fractions with standards
            if i % split_number[0] == 0 and blank == False:
                samplelistHeader["columns"] = [dict(flushMethod)]
                samplelistHeader["name"] = flushMethod["METHODNAME"]
                samplelistHeader["id"] = flushMethod["SAMPLENAME"] + str(i)
                samplelist["sampleLists"].append(dict(samplelistHeader))

                samplelistHeader["columns"] = [dict(STDMethod)]
                samplelistHeader["name"] = STDMethod["METHODNAME"]
                samplelistHeader["id"] = STDMethod["SAMPLENAME"] + str(i)
                samplelist["sampleLists"].append(dict(samplelistHeader))

            # Putting imported worklist into the subfraction method configuration
            subfractionMethod["SAMPLENAME"] = sample["SAMPLE"]
            subfractionMethod["SAMPLEDESCRIPTION"] = sample["SAMPLE_PLATE"]
            subfractionMethod["NOTES_STRING"] = sample["DESTINATION_PLATE"]
            subfractionMethod["#Sample Well"] = sample["SAMPLE_WELL"]
            subfractionMethod["#Fraction Well"] = sample["FRACTION_WELL"]
            subfractionMethod["#Start_FrCol"] = sample["START_FRCO"]
            subfractionMethod["#Stop_FrCol"] = sample["STOP_FRCOL"]
            samplelistHeader["columns"] = [dict(subfractionMethod)]
            samplelistHeader["name"] = subfractionMethod["SAMPLENAME"]
            samplelistHeader["id"] = subfractionMethod["SAMPLENAME"] + "-" + str(i)
            samplelist["sampleLists"].append(dict(samplelistHeader))

        # If no blanks put a standard and flush before the shutdown
        if blank == False:
            samplelistHeader["columns"] = [dict(flushMethod)]
            samplelistHeader["name"] = flushMethod["METHODNAME"]
            samplelistHeader["id"] = flushMethod["SAMPLENAME"] + str(i)
            samplelist["sampleLists"].append(dict(samplelistHeader))

            samplelistHeader["columns"] = [dict(STDMethod)]
            samplelistHeader["name"] = STDMethod["METHODNAME"]
            samplelistHeader["id"] = STDMethod["SAMPLENAME"] + str(i)
            samplelist["sampleLists"].append(dict(samplelistHeader))

        # Fills source plate with blanks
        for i in range(4):
            fillSourceplateMethod["#Fraction Well"] = 969 + i * 22
            samplelistHeader["columns"] = [dict(fillSourceplateMethod)]
            samplelistHeader["name"] = fillSourceplateMethod["SAMPLENAME"]
            samplelistHeader["id"] = subfractionMethod["SAMPLENAME"] + "-" + str(i)
            samplelist["sampleLists"].append(dict(samplelistHeader))

        samplelistHeader["columns"] = [dict(shutdownMethod)]
        samplelistHeader["name"] = shutdownMethod["METHODNAME"]
        samplelistHeader["id"] = shutdownMethod["SAMPLENAME"]
        samplelist["sampleLists"].append(dict(samplelistHeader))

        # Saving the samplelist to samplelistqueue.json
        samplelistqueue_path = Path(parent_dir + "//samplelistqueue.json")
        with open(samplelistqueue_path.absolute(), 'w') as f:
            json.dump(samplelist, f)
            f.close()

        # Saving the startupsamplelist in samplelist.json
        samplelist_path = Path(parent_dir + "//samplelist.json")
        with open(samplelist_path.absolute(), 'w') as f:
            json.dump({"sampleLists": [samplelist["sampleLists"][0]]}, f)
            f.close()

        return 200
