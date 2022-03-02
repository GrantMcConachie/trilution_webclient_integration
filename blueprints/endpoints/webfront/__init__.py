from flask import render_template, make_response
from flask_restx import Namespace, Resource
from pathlib import Path
import json
import time
# TODO: Change it so the webfront has a /4, /5 etc depending on the Gilson in order to use the skip/continue buttons
# Make sure to ask the user if they are sure that they are using the appropriate Gilson
# You would have to do the same with standardapp

namespace = Namespace("webfront", "Page to check on status of Gilson")

@namespace.route("/<string:hostname>")
class webfront(Resource):
    """webfront"""

    def get(self, hostname):
        """reads json files to make a list"""

        # Samplelist queue
        samplelistqueue_path = Path(".//reference_files//" + hostname + "//samplelistqueue.json")
        with open(samplelistqueue_path.absolute(), "r") as f:
            samplelist_queue = json.load(f)["sampleLists"]
            source_plate = samplelist_queue[0]["description"]
            f.close()

        # Current samplelist
        samplelist_path = Path(".//reference_files//" + hostname + "//samplelist.json")
        with open(samplelist_path.absolute(), "r") as f:
            current_samplelist = json.load(f)
            for i, method in enumerate(samplelist_queue):
                if method["id"] == current_samplelist["sampleLists"][0]["id"]:
                    current_place = i

            f.close()

        # Error log
        error_log_path = Path(".//reference_files//" + hostname + "//error_log.txt")
        with open(error_log_path.absolute(), "r") as f:
            error_log = f.readlines()
            f.close()

        return make_response(
            render_template(
                "status.html",
                samplelist_queue=samplelist_queue,
                current_samplelist=current_samplelist,
                current_place=current_place,
                error_log=error_log,
                source_plate=source_plate,
                hostname=hostname
            )
        )


@namespace.route("/skip_all/<string:hostname>")
class skip_all(Resource):
    """Edits the JSON flie to skip everything from the webfront."""

    def post(self, hostname):
        # import samplelist queue
        samplelistqueue_path = Path(".//reference_files//"  + hostname + "//samplelistqueue.json")
        with open(samplelistqueue_path.absolute(), "r") as f:
            samplelist_queue = json.load(f)
            f.close()

        # import current method
        current_sample_path = Path(".//reference_files//" + hostname + "//samplelist.json")
        with open(current_sample_path.absolute(), "r") as f:
            current_sample = json.load(f)
            current_sample_id = current_sample["sampleLists"][0]["id"]
            f.close()

        # Changing everything to SKIP except the shutdown method
        current = True
        for method in samplelist_queue["sampleLists"]:
            if current:
                if method["id"] == current_sample_id:
                    current = False
            elif method["id"] == "Stop":
                pass
            else:
                method["columns"][0]["SKIPPAUSE"] = "SKIP"

        # Writing the json files
        with open(samplelistqueue_path.absolute(), "w") as f:
            json.dump(samplelist_queue, f)
            f.close()

        return 200


@namespace.route("/skip_one/<string:id>/<string:hostname>")
class skip_one(Resource):
    """Edits JSON file to skip one method."""

    def post(self, id, hostname):
        # importing in the samplelist queue
        samplelistqueue_path = Path(".//reference_files//" + hostname + "//samplelistqueue.json")
        with open(samplelistqueue_path.absolute(), "r") as f:
            samplelist_queue = json.load(f)
            f.close()

        # Changing the clicked button to skip
        for method in samplelist_queue["sampleLists"]:
            if id == method["id"]:
                if method["columns"][0]["SKIPPAUSE"] == "SKIP":
                    method["columns"][0]["SKIPPAUSE"] = "RUN"
                elif method["columns"][0]["SKIPPAUSE"] == "RUN":
                    method["columns"][0]["SKIPPAUSE"] = "SKIP"

        # Writing the json file
        with open(samplelistqueue_path.absolute(), "w") as f:
            json.dump(samplelist_queue, f)
            f.close()

        return 200

@namespace.route("/continue_run/<string:hostname>")
class continue_run(Resource):
    """Picks up where the run left off after an error"""

    def post(self, hostname):
        samplelistqueue_path = Path(".//reference_files//" + hostname + "//samplelistqueue.json")
        with open(samplelistqueue_path.absolute(), "r") as f:
            samplelist_queue = json.load(f)
            startup_method = dict(samplelist_queue["sampleLists"][0])
            startup_method["id"] = startup_method["id"] + str(time.time())
            f.close()

        # Going through the queue changing everything back to run, adding a flush and a startup
        for i, method in enumerate(reversed(samplelist_queue["sampleLists"])):
            if method['id'] == 'Stop':
                pass

            elif method['name'] == '4ML_10mm_FLUSH_Subfraction':
                flush_method = dict(method)
                flush_method["id"] = flush_method["id"] + str(time.time())
                method['columns'][0]['SKIPPAUSE'] = "RUN"

            elif method['columns'][0]['SKIPPAUSE'] == 'SKIP':
                method['columns'][0]['SKIPPAUSE'] = "RUN"

            elif method['columns'][0]['SKIPPAUSE'] == 'RUN':
                samplelist_queue["sampleLists"].insert(-i, startup_method)
                samplelist_queue["sampleLists"].insert(-i, flush_method)
                break
        
        # Starting from where we left off
        current_sample_path = Path(".//reference_files//" + hostname + "//samplelist.json")
        with open(current_sample_path.absolute(), "w") as f:
            json.dump({"sampleLists": [startup_method]}, f)
            f.close()

        with open(samplelistqueue_path.absolute(), "w") as f:
            json.dump(samplelist_queue, f)
            f.close()

        return 200