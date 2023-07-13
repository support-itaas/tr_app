import json

import requests

from odoo import fields, models, api,exceptions, _
...
from odoo.exceptions import UserError


class WizardInquiry(models.Model):
    _name = "wizard.inquiry"

    transactionDate=fields.Date(string="Transaction Date" ,required=True)
    reference = fields.Char(string="Reference" ,required=True)
    transaction_id = fields.Char(string="Transaction ID" ,required=True)


    def inquiry_verification(self):
        transaction_date = self.transactionDate
        partner_transaction_id=self.transaction_id
        reference_1=self.reference

        IrDefault = self.env['ir.default'].sudo()
        scb_api_key = IrDefault.get(
            'res.config.settings', "scb_api_key")
        scb_api_secret = IrDefault.get(
            'res.config.settings', "scb_api_secret")

        biller_id = IrDefault.get(
            'res.config.settings', "biller_id")

        url = "https://api-uat.partners.scb/partners/v1/oauth/token"
        payload = json.dumps({
            "applicationKey": scb_api_key,
            "applicationSecret": scb_api_secret
        })
        headers = {
            'Content-Type': 'application/json',
            'resourceOwnerId': scb_api_key,
            'requestUId': '51c0f021-f1e4-4abf-bf7f-79bff4fbe9f6',
            'accept-language': 'EN',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        parsed_response = json.loads(response.text)
        # Extract the accessToken value
        access_token = parsed_response['data']['accessToken']

        url = "https://api-uat.partners.scb/partners/v1/payment/billpayment/inquiry?billerId="+biller_id+"&reference1="+reference_1+"&transactionDate="+transaction_date+"&eventCode=00300100"
        payload = {}
        headers = {
            'authorization': 'Bearer ' + access_token,
            'requestUID': '871872a7-ed08-4229-a637-bb7c733305db',
            'resourceOwnerID': scb_api_key,
            'accept-language': 'EN',
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        parsed_response = json.loads(response.text)
        response_dis = parsed_response['status']['description']

        if response_dis == 'Success':
            raise exceptions.except_orm(_("SUCCESS"), _(response_dis))
        else:
            raise exceptions.except_orm(_("FAILED"), _(response_dis))
