''' Not Used in API, can be implemented if needed '''

from flask_restx import Namespace, Resource, fields

# adds the /sampleverification section and allows GET calls

namespace = Namespace('sampledataverification', 'Allows Trilustion to be able to verify its data (NOT USED)')

# Model of the data that needs to be returned
returndata_model = namespace.model('returndata', {
    "sampleDataVerification":fields.Nested(
        namespace.model('data', {
            "sampleName":fields.String,
            "sampleDataId":fields.String,
            "createdBy":fields.String,
            "sampleDescription":fields.String,
            "runDate":fields.String,
            "state":fields.String,
            "passFail":fields.String,
            "verificationData":fields.Nested(
                namespace.model('verificationdata', {
                    "metadata":fields.Nested(
                        namespace.model('metadata', {
                            "passFail":fields.String
                        })
                    )
                })
            )
        })
    )
})

# an example for documentation DELETE LATER
return_example = {
    "sampleDataVerification":{
        "sampleName":"hello",
        "sampleDataId":"test",
        "createdBy":"This is a test",
        "sampleDescription":"testing",
        "runDate":"idk",
        "state":"what",
        "passFail":"to",
        "verificationData":{
            "metadata":{
                "passFail":"put"
            }
        }
    }
}

@namespace.route('/<int:id>')
class sampleverification_id(Resource):
    '''Allows Trilution to call for data when it needs is'''

    @namespace.response(500, 'Internal Server Error.')
    @namespace.marshal_with(returndata_model) #documentation purposes
    def get(self, id):
        '''returns a specific data dependent on the id that gilson wants'''

        return return_example