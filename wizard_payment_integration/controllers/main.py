# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

import base64
from werkzeug.utils import redirect
import requests
import json
from odoo.loglevels import ustr
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from odoo import http
from odoo.http import request, Response, JsonRequest, HttpRequest, Root


class JsonRequestNew(JsonRequest):

    def _json_response(self, result=None, error=None):
        response = {
            'jsonrpc': '2.0',
            'id': self.jsonrequest.get('id')
        }
        if error is not None:
            response['error'] = error
        if result is not None:
            is_dict = isinstance(result, dict)
            if is_dict:
                if 'flag' in result:
                    del result['flag']
                    response = result
                else:
                    response['result'] = result
            else:
                response['result'] = result
        if self.jsonp:
            response['session_id'] = self.session.sid
            mime = 'application/javascript'
            body = "%s(%s);" % (self.jsonp, json.dumps(response, default=ustr),)
        else:
            mime = 'application/json'
            body = json.dumps(response, default=ustr)

        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )


class RootNew(Root):

    def get_request(self, httprequest):
        if httprequest.args.get('jsonp'):
            return JsonRequestNew(httprequest)
        if httprequest.mimetype in ("application/json", "application/json-rpc"):
            return JsonRequestNew(httprequest)
        else:
            return HttpRequest(httprequest)


http.root = RootNew()


class WizardPayment(http.Controller):

    @http.route(['/wizard_payment_method/<int:order_id>'], auth="user", website=True)
    def wizard_payment_method(self, **kw):
        request.session.update({'order_id': kw.get('order_id')})
        return request.render('wizard_payment_integration.wizard_payment_method')

    @http.route(['/wizard_gbpay_method_submit'], auth="public", website=True)
    def wizard_gbpay_method_submit(self, **kw):
        # request.session.update({'order_id': kw.get('order_id')})
        method_payment = kw.get('payment_select')
        if method_payment == "installment":
            return redirect('wizard_gbpay_installment_submit')
        elif method_payment == "credit":
            return request.render('wizard_payment_integration.wizard_payment_form')

    @http.route(['/wizard_gbpay_installment_submit'], auth="public", website=True)
    def wizard_gbpay_installment_submit(self, **kw):
        # re
        # request.session.update({'order_id': kw.get('order_id')})
        baseurl = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        order_id = request.env['pos.order'].search([('id', '=', int(request.session.get('order_id')))])
        order_name = order_id.name.replace(' ', '')
        IrDefault = request.env['ir.default'].sudo()
        gbp_public_key = IrDefault.get(
            'res.config.settings', "gbp_public_key")
        gbp_secret_key = IrDefault.get(
            'res.config.settings', "gbp_secret_key")
        amount = "%.2f" % order_id.amount_total
        return request.render('wizard_payment_integration.wizard_payment_installment_form',
                              {'order_name': order_name, 'gbp_public_key': gbp_public_key, 'amount': amount,
                               'gbp_secret_key': gbp_secret_key,
                               'response_url': str(baseurl) + '/success',
                               'background_url': str(baseurl) + '/success', })

        # <--------------GBPRIME------------------->

    @http.route(['/payment_details'], auth="user", website=True, type='http', sitemap=True, csrf=False)
    def wizard_payment_details(self, **post):
        order = request.env['pos.order'].browse(request.session.get('order_id'))
        if order.partner_id.street and order.partner_id.city and order.partner_id.state_id and order.partner_id.zip and order.partner_id.country_id:
            IrDefault = request.env['ir.default'].sudo()
            gbp_public_key = IrDefault.get(
                'res.config.settings', "gbp_public_key")
            gbp_secret_key = IrDefault.get(
                'res.config.settings', "gbp_secret_key")
            if not gbp_public_key or not gbp_secret_key:
                return "Payment declined. Please contact you merchant"

            url = "https://api.globalprimepay.com/v2/tokens"
            pk = gbp_public_key + ':'
            pk_bytes = bytes(pk, 'utf-8')
            payload = json.dumps({
                "rememberCard": False,
                "card": {
                    "number": post.get('card_number'),
                    "expirationMonth": post.get('expiry_month'),
                    "expirationYear": post.get('expiry_year'),
                    "securityCode": post.get('cvv'),
                    "name": post.get('holder_name')
                }
            })
            encoded_key = base64.b64encode(pk_bytes)
            decoded_key = encoded_key.decode("utf-8")
            headers = {
                'Authorization': 'Basic ' + decoded_key,
                'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            response_data = json.loads(response.text)
            card_data = response_data.get('card')
            token = card_data.get('token')
            request.session.update({
                'token': token,
                'gbp_public_key': gbp_public_key,
                'gbp_secret_key': gbp_secret_key
            })
            return request.render('wizard_payment_integration.wizard_payment_details', {
                'amount': int(order.amount_total),
                'ref': order.name,
                'details': [line.product_id.name for line in order.lines]
            })
        else:
            return "Please add an address"

    @http.route(['/verification'], auth="user", website=True)
    def wizard_payment_verification(self, **kw):
        baseurl = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        order = request.env['pos.order'].browse(request.session.get('order_id'))
        gbp_public_key = request.session.get('gbp_public_key')
        gbp_secret_key = request.session.get('gbp_secret_key')
        token = request.session.get('token')
        sk = gbp_secret_key + ':'
        sk_bytes = bytes(sk, 'utf-8')
        encoded_key = base64.b64encode(sk_bytes)
        decoded_key = encoded_key.decode("utf-8")
        url = "https://api.globalprimepay.com/v2/tokens/charge"
        address = order.partner_id.street or '' + ',' + order.partner_id.city or '' + order.partner_id.state_id.name or '' + order.partner_id.zip or '' + ',' + order.partner_id.country_id.name or ' '
        payload = json.dumps({
            "amount": float(kw.get('amount')),
            "referenceNo": str(kw.get('ref')),
            "detail": kw.get('details'),
            "customerName": order.partner_id.name,
            "customerEmail": order.partner_id.email,
            "customerAddress": address,
            "customerTelephone": order.partner_id.mobile,
            "merchantDefined1": "Promotion",
            "card": {
                "token": token
            },
            "otp": "Y",
            "responseUrl": str(baseurl) + '/success',
            "backgroundUrl": str(baseurl) + '/success'
        })
        headers = {
            'Authorization': 'Basic ' + decoded_key,
            'Content-Type': 'application/json',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response_data = json.loads(response.text)
        if response_data.get('resultCode') == '00':
            gbp_reference = response_data.get('gbpReferenceNo')

            url = "https://api.globalprimepay.com/v2/tokens/3d_secured"
            payload = 'publicKey=' + gbp_public_key + '&gbpReferenceNo=' + gbp_reference
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            otp_response = requests.request("POST", url, headers=headers, data=payload)
            return request.render('wizard_payment_integration.payment_verification',
                                  {'response_data': otp_response.text})
        else:
            return "PAYMENT ALREADY DONE FOR THIS ORDER"

    @http.route(['/payment_cancel'], csrf=False, auth="user", website=True)
    def payment_cancel(self, **kw):
        return request.render('wizard_payment_integration.payment_cancel')

    @http.route(['/success'], csrf=False, auth="user", website=True)
    def wizard_payment_success(self, **kw):
        request.session.update({'trans_response': kw})
        if kw.get('resultCode') == '00':
            order = request.session.get('order_id')
            order_id = request.env['pos.order'].browse(order)
            journal_id = request.env['account.journal'].search([('name', '=', "GBPay"), ('code', '=', "GBP")])
            # from datetime import date
            # payment_date = date.today()
            # from datetime import datetime
            # create_date = datetime.now()
            data = order_id.read()[0]
            data['journal_id'] = journal_id.id
            data['amount'] = order_id.amount_total
            data['statement_id'] = order_id.session_id.statement_ids.ids[0]
            # data = {'session_id': (order_id.session_id.id, order_id.session_id.name),
            #         'journal_id': (scb_success_calljournal_id.id, journal_id.name), 'amount': int(order_id.amount_total),
            #         'payment_name': False, 'payment_date': str(payment_date),
            #         'create_uid': (order_id.session_id.user_id.id, order_id.session_id.user_id.name),
            #         'create_date': str(create_date),
            #         'write_uid': (order_id.session_id.user_id.id, order_id.session_id.user_id.name),
            #         'write_date': str(create_date), 'journal': journal_id.id,
            #         'statement_id': order_id.session_id.statement_ids.ids[0]}
            order_id.is_payment_failed = False
            order_id.add_payment(data)
            order_id.action_pos_order_paid()
            return request.render('wizard_payment_integration.payment_success', {'order_id': order_id.id})
        else:
            return redirect('/failed')

    @http.route(['/failed'], csrf=False, auth="user", website=True)
    def wizard_payment_failed(self, **kw):
        order = request.session.get('order_id')
        order_id = request.env['pos.order'].search([('id', '=', order)])
        order_id.is_payment_failed = True
        return request.render('wizard_payment_integration.payment_failed', {'order': order})

        # <--------------SCB------------------>

    @http.route('/scb_success_call', type='json', auth="none", methods=['POST'])
    def scb_success_call(self, request=None, **kw):
        data = {}
        if request.httprequest.data:
            data = request.httprequest.data
            data = data.decode()
            data = json.loads(data)
        pos_ref = data.get('billPaymentRef1')
        order_id = request.env['pos.order'].sudo().search([('name_ref', '=', pos_ref)])
        if order_id:
            order_id.state = 'paid'
        return_data = {
            "resCode": "00",
            "resDesc ": "success",
            "transactionId": data.get('transactionId'),
            "confirmId": "",
            "flag": 1
        }
        transactionId = data.get('transactionId')
        request.env['scb.log'].sudo().create({'name': transactionId, 'scb_data': data})
        return return_data
