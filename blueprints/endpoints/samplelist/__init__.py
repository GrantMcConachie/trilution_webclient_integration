from flask_restx import Namespace, Resource, fields
import json
from pathlib import Path

# Creates the endpoint
namespace = Namespace('samplelist', 'Receievs a samplelist from Gilson.PlateChecker and then gives that samplelist to Trilutoin.')

# Example of a sample list for documentation
samplelist_example = namespace.model('sampleList_example', {
    "sampleList":fields.Nested(namespace.model('sampleList', {
        "name":fields.String,
        "id":fields.String,
        "createdBy":fields.String,
        "description":fields.String,
        "createDate":fields.String,
        "startDate":fields.String,
        "endDate":fields.String,
        "columns":fields.List(fields.Nested(namespace.model('columns', {
            "METHODNAME":fields.String,
            "SAMPLENAME":fields.String,
            "SAMPLEDESCRIPTION":fields.String,
        })))
    }))
})

samplelists_example = namespace.model('sampleLists_example', {
    "sampleLists":fields.List(fields.Nested(namespace.model('sampleLists', {
        "name":fields.String,
        "id":fields.String, # What is requested in the next GET 
        "createdBy":fields.String,
        "description":fields.String,
        "createDate":fields.String,
        "startDate":fields.String,
        "endDate":fields.String,
        "columns":fields.String(required=False)
    })))
})

@namespace.route('/<string:id>/<string:hostname>')
class samplelist_id(Resource):
    '''Finds a specific samplelist by searching for a unique ID'''

    @namespace.response(500, 'Internal Server Error')
    #@namespace.marshal_with(samplelist_example)
    def get(self, id, hostname):
        '''Returns the sample list
        TO TEST: hostname is GILSON_#. The id is arbitrary.
        '''

        samplelists_path = Path(".//reference_files//" + hostname + "//samplelist.json")
        with open(samplelists_path.absolute(), 'r') as f:
            samplelists = json.load(f)
            samplelist = {"sampleList": samplelists["sampleLists"][0]}
            f.close()
        
        return samplelist

@namespace.route('/<string:hostname>')
class get_samplelists(Resource):
    '''Route for getting list of samplelists (however it's going to be 1)'''

    @namespace.response(500, 'Internal Server Error.')
    @namespace.marshal_with(samplelists_example)
    def get(self, hostname):
        '''returns list of sample lists (There is only one and returns exacly what the other GET returns)
        TO TEST: hostname is GILSON_#
        '''

        # Load the samplelists from samplelist.json
        samplelists_path = Path(".//reference_files//" + hostname + "//samplelist.json")
        with open(samplelists_path.absolute(), 'r') as f:
            samplelists = json.load(f)
            f.close()

        return samplelists
