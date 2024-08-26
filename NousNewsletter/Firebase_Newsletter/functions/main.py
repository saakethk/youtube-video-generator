
""" Required Dependencies """
from firebase_functions.firestore_fn import (
  on_document_created,
  Event,
  Change,
  DocumentSnapshot,
)
from mailjet_rest import Client

""" Helper Functions """

class MailjetAPI():
    
    # Vars necessary for interacting with API
    def __init__(self):
        self.api_key = '4983303363ad2adf882fa58a0f0184fc'
        self.api_secret = 'b0b1cfd75bc81e8789910955ea9679e8'
        self.mailjet = Client(auth=(self.api_key, self.api_secret), version='v3.1')
    
    # Sends Welcome Template email via Mailjet API
    def sendWelcomeEmail(self, email: str, firstname: str, lastname: str, sub_id: int):
        
        data = {
          'Messages': [
                {
                    "To": [
                        {
                            "Email": email,
                            "Name": f"{firstname} {lastname}"
                        }
                    ],
                    "Data": {
                      "firstname": firstname,
                      "sub_id": sub_id
                    },
                    "TemplateID": 6216118,
                    "TemplateLanguage": True
                }
            ]
        }
        
        self.mailjet.send.create(data=data)

""" Firebase Functions """
# The Google Cloud Config for this function is 1 vCPU and 256 Mi (mibibyte)
# Triggers on new user creation
# Firebase function which sends out welcome email when necessary
@on_document_created(document="subscriptions/{subscriptionId}")
def sendWelcomeEmail(event: Event[DocumentSnapshot]) -> None:
    
    # Retrieves helper functions for Mailjet
    mailjet = MailjetAPI()

    # Retrieves document details
    data = event.data.to_dict()

    mailjet.sendWelcomeEmail(
        email=data["email"],
        firstname=data["first_name"],
        lastname=data["last_name"],
        sub_id=data["sub_num"]
    )

def test():
    # Retrieves helper functions for Mailjet
    mailjet = MailjetAPI()

    mailjet.sendWelcomeEmail(
        email="saakethr.kesireddy@gmail.com",
        firstname="saaketh",
        lastname="kesireddy",
        sub_id=0
    )

test()