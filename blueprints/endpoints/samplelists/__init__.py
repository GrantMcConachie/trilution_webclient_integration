''' Not Used in API, can be implemented if needed '''

from flask_restx import Namespace, Resource, fields

# Creates the endpoint
namespace = Namespace('samplelists', 'Endpoint for Gilson to recieve samplelists')

# Example of what we return for documentation
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

# What I need to retun to Gilson example
return_example = {
    "sampleLists": [
        {             
            "name":"Test Sample List",
            "id":"31",
            "createdBy":"System",
            "description":"Test Sample List",
            "createDate":"2019-03-19T09:45:11.16",
            "startDate":"2021-10-22T09:30:00.00",
            "endDate":"2021-10-22T09:30:00.00",
            "columns":[{
                "SKIPPAUSE":"RUN",
                "METHODNAME":"Test Method",
                "SAMPLENAME":"Sample Test 1",
                "SAMPLEAMOUNT":0,
                "SAMPLEDESCRIPTION":"Test",
                "SAMPLEID":"00000000-0000-0000-0000-000000000000",
                "INJECTIONYESNO":"YES",
                "PEAKINFORMATION":"UNKNOWN",
                "NOTES_STRING":"318",
                "#Sample Well":"1"
            }]
        },
        {        
            "name":"Test Sample List 2",
            "id":"36",
            "createdBy":"System",
            "description":"Test Sample List 2",
            "createDate":"2019-03-19T09:45:11.16",
            "startDate":"2021-10-22T09:30:00.00",
            "endDate":"2021-10-22T09:30:00.00",
            "columns": None
        }
    ]
}

@namespace.route('')
class id(Resource):
    '''Allows Trilution to call for data when it needs is'''

    @namespace.response(500, 'Internal Server Error.')
    @namespace.marshal_with(samplelists_example)
    def get(self):
        '''returns list of sample lists'''

        return return_example

@namespace.route('/<string:id>')
class samplelists_id(Resource):
    '''Samplelist validation'''

    @namespace.response(500, 'Internal Server Error.')
    @namespace.response(200, 'success')
    #@namespace.expect(samplelists_validation_ex) TODO
    def post(self, id):
        '''Place for samplelist validation'''
        pass