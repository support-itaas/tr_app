import json

import requests

from odoo import fields, models, api,exceptions, _
...
from odoo.exceptions import UserError


class WizardSlipVerification(models.Model):
    _name = "wizard.slip.verification"

    trn_ref=fields.Char(string="Transaction Ref" ,required=True)


    def payment_slip_verification(self, data):
        transref = self.trn_ref
        IrDefault = self.env['ir.default'].sudo()
        scb_api_key = IrDefault.get(
            'res.config.settings', "scb_api_key")
        scb_api_secret = IrDefault.get(
            'res.config.settings', "scb_api_secret")
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
        try:
            access_token = parsed_response['data']['accessToken']
            url = "https://api-uat.partners.scb/partners/v1/payment/billpayment/transactions/%s?sendingBank=014" % (
                transref)
            payload = {}
            headers = {
                'authorization': 'Bearer ' + access_token,
                'requestUID': 'ab3568c5-e058-4c7e-ac98-7fdc7924a67b',
                'resourceOwnerID': scb_api_key,
                'accept-language': 'EN',
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            parsed_response = json.loads(response.text)
            response_dis = parsed_response['status']['description']
            # return response
            if response_dis == 'Success':
                raise exceptions.except_orm(_("SUCCESS"), _(response_dis))
            else:
                raise exceptions.except_orm(_("FAILED"), _(response_dis))
        except:
            print(parsed_response['status']['description'])
            raise UserError(_('Please check your Api key or Api Secret'))





