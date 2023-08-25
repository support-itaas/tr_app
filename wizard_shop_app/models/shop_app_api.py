# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.
import json
from datetime import date, datetime
from PIL import Image
import os
import pathlib
from io import BytesIO
import base64
import requests
from odoo import api, fields, models, _


class WizardShopApi(models.Model):
    _name = 'wizard.shop.api'

    def get_initialize(self, payload):
        data = {}
        build_version = payload.get('build_version')
        branch = payload.get('branch')
        shop_user = payload.get('shop_user')
        if build_version:
            active_version = self.env['ir.config_parameter'].get_param('active_build_version')
            if active_version == build_version:
                data.update({'current_build': active_version})
            else:
                return {"success": "false", "message": "Please update the app to the latest version",
                        "data": [{"current_build": active_version}]}
        else:
            return {"success": "false", "message": "parameter build version required",
                    "data": []}
        if branch:
            branch_id = self.env['project.project'].search([('id', '=', branch)])
            if not branch_id:
                return {"success": "false", "message": "Branch not found", "data": []}
            service_list = []
            services = self.env['project.service'].search([('project_id.id', '=', branch)])
            if services:
                for service in services:
                    minutes = service.duration * 60
                    format_minutes = "{:.2f}".format(minutes)
                    format_minutes = float(format_minutes)
                    # duration = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(service.duration) * 60, 60))
                    service_data = {
                        'id': service.product_id.id, 'name': service.product_id.name,
                        'img': service.product_id.image_medium,
                        'price': service.product_id.lst_price, 'signal': service.signal, 'duration': format_minutes,
                        'currency': service.product_id.company_id.currency_id.symbol
                    }
                    service_list.append(service_data)
                data.update({'services': service_list})
            else:
                return {"success": "false", "message": "No Services found for the branch", "data": service_list}

            if branch_id:
                if branch_id.qr_code:
                    data.update({'static_qr_code': branch_id.qr_code})
                else:
                    return {"success": "false", "message": "QR Code not added for this branch", "data": []}
            else:
                return {"success": "false", "message": "Cant find branch", "data": []}

        else:
            return {"success": "false", "message": "parameter branch id required", "data": []}
        if shop_user:
            shop_user_id = self.env['res.partner'].search([('user_ids.id', '=', shop_user)])
            if shop_user_id:
                data.update({"shop_user_details": [
                    {'img': shop_user_id.image, "name": shop_user_id.name, "id": shop_user_id.id}]})
                return {"success": "true", "message": "Initialization success", "data": data}
            else:
                return {"success": "false", "message": "Shop user not found", "data": []}
        else:
            return {"success": "false", "message": "parameter shop user id required", "data": []}

    # def fetch_services_by_branch(self, branch=None):
    #
    #     service_list = []
    #     services = self.env['project.service'].search([('project_id', '=', branch)])
    #     if services:
    #         # services = self.env['product.product'].search([('is_service', '=', True), ])
    #         for service in services:
    #             service_data = {
    #                 'id': service.product_id.id, 'name': service.product_id.name,
    #                 'img': service.product_id.image_medium,
    #                 'price': service.product_id.lst_price
    #             }
    #             service_list.append(service_data)
    #         return {"success": "true", "message": "Services retrieved", "data": service_list}
    #     else:
    #         return {"success": "false", "message": "No Services found for this branch", "data": service_list}

    # def get_active_session(self, branch=None):
    #     if branch:
    #         active_pos_session = self.env['pos.config'].search(
    #             []).filtered(lambda s: s.current_session_state == 'opened' and s.branch_id.id == branch)
    #         if active_pos_session:
    #             return {"success": "true", "message": "Active session retrieved",
    #                     "data": [{"active_pos_session": active_pos_session.id}]}
    #         else:
    #             return {"success": "false", "message": "No active session found",
    #                     "data": []}
    #     else:
    #         return {"success": "false", "message": "please provide branch id in parameter",
    #                 "data": []}

    # def search_services(self, service_name):
    #     services = self.env['product.product'].search([('is_service', '=', True), ('name', 'ilike', service_name)])
    #
    #     return {'success': "true" if services else "false",
    #             "message": "Search results retrieved" if services else "Service not available",
    #             "data": services.ids or []}

    # def user_authentication(self, data):
    #     url = "http://localhost:8069/web/session/authenticate"
    #     payload = json.dumps({
    #         "jsonrpc": "2.0",
    #         "method": "call",
    #         "id": 1,
    #         "params": {
    #             "db": data.get('db_name'),
    #             "login": data.get('email'),
    #             "password": data.get('password'),
    #             "base_location": "http://localhost:8069",
    #             "context": {}
    #         }
    #     })
    #     headers = {
    #         'Content-Type': 'application/json',
    #     }
    #
    #     response = requests.request("POST", url, headers=headers, data=payload)
    #     response = json.loads(response.text)
    #     return response.get('result')

    def user_validation(self, data):
        response = {}
        if not data.get('email'):
            return {'success': 'False', 'message': "Please provide email in parameter", "data": []}
        if not data.get('password'):
            return {'success': 'False', 'message': "Please provide password", "data": []}
        if not data.get('service'):
            return {'success': 'False', 'message': "Please provide service id in parameter", "data": []}
        user_email = self.env['res.partner'].search(
            [('email', '=', data.get('email'))])
        user_password = self.env['res.partner'].search(
            [('password', '=', data.get('password'))])
        if not user_email and not user_password:
            return {'success': 'False', 'message': "Both email and password are wrong", "data": []}
        if not user_email:
            return {'success': 'False', 'message': "User with this email address not found", "data": []}
        if not user_password:
            return {'success': 'False', 'message': "Wrong password", "data": []}
        user_id = self.env['res.partner'].search(
            [('email', '=', data.get('email')), ('password', '=', data.get('password'))])
        service_id = self.env['product.product'].search(
            [('id', '=', data.get('service')), ('is_service', '=', True)])
        if user_id and service_id:
            # active_pos_session = self.env['pos.config'].search(
            #     []).filtered(lambda s: s.current_session_state == 'opened' and s.branch_id.id == data.get('branch_id'))
            # active_pos_session = active_pos_session.filtered(lambda s: s.current_session_state == 'opened' and s.branch_id.id == data.get('branch_id'))
            # print("active",active_pos_session)
            # w
            # for session in active_pos_session:
            #     print("current_session_state",session.current_session_state)
            #     if session.current_session_state == 'opened' and session.branch_id == data.get('branch_id'):
            #         print("session",session, session.current_session_state)
            #         print("vranch",session.branch_id.id)
            # print("active_pos_session",active_pos_session)
            # w
            # active_pos_session = data.get('active_pos_session')
            # if active_pos_session:
            # order = self.env['pos.session'].create(
            #     {'config_id': active_pos_session.id,
            #      'order_ids': [(0, 0, {'lines': [(0, 0,
            #                                       {'product_id': service_data.id, 'qty': 1,
            #                                        'product_uom': service_data.uom_id.id,
            #                                        'price_unit': service_data.list_price})]},)]})
            # order = self.env['pos.order'].create(
            #     {'partner_id': user.id, 'branch_id': data.get('branch_id'),
            #      'lines': [(0, 0,
            #                 {'product_id': service_data.id,
            #                  'qty': 1,
            #                  'product_uom': service_data.uom_id.id,
            #                  'price_unit': service_data.list_price})]})
            # order.write({"name": order.session_id.config_id.sequence_id._next()})
            # else:
            #     return {'success': 'False', 'message': 'No Active Sessions'}

            response.update(
                {'success': "true", "message": "User validated",
                 "data": [{"user": user_id.id, "service": service_id.id}]})
        # elif not user_id and service_id:
        #     response.update(
        #         {'success': 'False', 'message': "Authentication Failed due to user credentials mismatch", "data": []})
        elif user_id and not service_id:
            response.update(
                {'success': 'False', 'message': "Invalid service id parameter", "data": []})
        return response

    def create_order_and_payment(self, data):
        branch = data.get('branch')
        shop_user = data.get('shop_user')
        service = data.get('service')
        payment_method = data.get('payment_method')
        client_order_id = data.get('client_order_id')
        payment_date = data.get('payment_date')
        from datetime import datetime
        order_date = datetime.strptime(payment_date, '%Y-%m-%d %H:%M:%S')
        order_id = self.env['pos.order'].search([('client_order_id', '=', client_order_id)])
        if order_id:
            return {'success': 'False', 'message': 'Duplicate transaction', 'data': []}
        # active_pos_session = data.get('active_pos_session')
        if not shop_user:
            return {'success': 'False', 'message': 'Please provide shop user id in parameter', 'data': []}
        elif not service:
            return {'success': 'False', 'message': 'Please provide service id in parameter', 'data': []}
        # elif not active_pos_session:
        #     return {'success': 'False', 'message': 'Please provide active pos session id in parameter', 'data': []}
        elif not branch:
            return {'success': 'False', 'message': 'Please provide branch id in parameter', 'data': []}
        elif not payment_method:
            return {'success': 'False', 'message': 'Please provide a payment method in parameter', 'data': []}
        elif not payment_date:
            return {'success': 'False', 'message': 'Please provide a payment date in parameter', 'data': []}
        else:
            # print ('shop_user----',shop_user)
            shop_user = 399
            # print('DATA---',data)
            # user_id = self.env['res.partner'].sudo().search([('user_ids.id', '=', shop_user)], limit=1)
            user_id = self.env['res.partner'].sudo().search([('user_ids.id', '=', shop_user)],limit=1)
            service_id = self.env['product.product'].sudo().search([('id', '=', service)],limit=1)
            branch_id = self.env['project.project'].sudo().search([('id', '=', branch)],limit=1)


            # active_pos_session_id = self.env['pos.config'].sudo().search(
            #     []).filtered(lambda s: s.current_session_state == 'opened' and s.branch_id.id == branch_id.id)

            if not user_id:
                return {'success': 'False', 'message': 'User not found', 'data': []}
            elif not service_id:
                return {'success': 'False', 'message': 'Service not found', 'data': []}
            elif not branch_id:
                return {'success': 'False', 'message': 'Branch not found', 'data': []}
            # elif not active_pos_session_id:
            #     return {'success': 'False', 'message': 'No active pos sessions', 'data': []}
            else:
                order_id = self.env['pos.order'].create(
                    {'partner_id': user_id.id, 'branch_id': branch_id.id, 'date_order': order_date,
                     'client_order_id': client_order_id,
                     'lines': [(0, 0,
                                {'product_id': service_id.id,
                                 'qty': 1,
                                 'product_uom': service_id.uom_id.id,
                                 'price_unit': service_id.list_price})]})
                if order_id:
                    order_id.write({"name": order_id.session_id.config_id.sequence_id._next()})
                    if payment_method == "offline":
                        journal_id = self.env['account.journal'].search(
                            [('name', '=', "Offline"), ('code', '=', "OFF")])
                    elif payment_method == 'qr':
                        journal_id = self.env['account.journal'].search(
                            [('name', '=', "QR"), ('code', '=', "QRC")])
                    elif payment_method == 'redeem':
                        journal_id = self.env['account.journal'].search(
                            [('name', '=', "Redeem"), ('code', '=', "REDM")])
                    else:
                        return {'success': 'False', 'message': 'Journal not found', 'data': []}
                    # from datetime import date
                    payment_date = order_date.date()
                    # from datetime import datetime
                    create_date = order_date
                    data = order_id.read()[0]
                    data['journal'] = journal_id.id
                    data['amount'] = order_id.amount_total
                    print ('DATA to ADD Payment---',data)
                    # data = {'session_id': (order_id.session_id.id, order_id.session_id.name),
                    #         'journal_id': (journal_id.id, journal_id.name), 'amount': int(order_id.amount_total),
                    #         'payment_name': False, 'payment_date': str(payment_date),
                    #         'create_uid': (order_id.session_id.user_id.id, order_id.session_id.user_id.name),
                    #         'create_date': str(create_date),
                    #         'write_uid': (order_id.session_id.user_id.id, order_id.session_id.user_id.name),
                    #         'write_date': str(create_date), 'journal': journal_id.id,
                    #         'statement_id': order_id.session_id.statement_ids.id}
                    order_id.add_payment(data)
                    if payment_method in ['offline', 'redeem']:
                        order_id.action_pos_order_paid()
                    return {"success": "true", "message": "Order and Payment created",
                            "data": [{"order_id": order_id.id, "payment_id": order_id.statement_ids.ids,
                                      "payment_amount": order_id.amount_paid}]}
                else:
                    return {"success": "false", "message": "Couldn't create order", "data": []}

    # def user_account_details(self, user_id):
    #     user = self.env['res.users'].search([('id', '=', user_id)])
    #     return {"success": "true" if user else "false",
    #             'message': "Retrieved user account details",
    #             "data": [{'img': user.image, "name": user.name, "id": user.id}]}

    def payment_slip_verification(self, data):
        transref = data.get('transref')
        sendingbank = data.get('sendingbank')
        url = 'https://api-uat.partners.scb/partners/v1/payment/billpayment/transactions/{' + transref + '}?sendingBank=' + sendingbank + ' '
        # url = 'https://api-sandbox.partners.scb/partners/sandbox/v1/payment/billpayment/transactions/{' + transref + '}?sendingBank=' + sendingbank + ' '
        payload = {}
        headers = {
            'authorization': 'Bearer 994f52ea-ef3d-4328-a073-591f95fcc38c',
            'requestUID': 'ab3568c5-e058-4c7e-ac98-7fdc7924a67b',
            'resourceOwnerID': 'l7945d71c7c4e34fe686520160e5268518',
            'accept-language': 'EN',
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        return response

    def get_branch_data(self):
        branches = self.env['project.project'].search([('is_branch', '=', True)])
        data = []
        for branch in branches:
            branch_data = {'id': branch.id, 'name': branch.name}
            data.append(branch_data)
        return {'success': "true" if branches else "false",
                'message': "Retrieved list of branch ids" if branches else "No branches found",
                "data": data or []
                }

    def fetch_online_qr_code(self, data):
        order = data.get('order')
        if not order:
            return {"success": "false", "message": "Please provide order id in parameter", "data": []}
        order_id = self.env['pos.order'].search([('id', '=', order)])
        if order_id.amount_total == 0:
            return {"success": "false", "message": "Order total amount is zero", "data": []}
        if not order_id:
            return {"success": "false", "message": "Order not found", "data": []}
        IrDefault = self.env['ir.default'].sudo()
        scb_api_key = IrDefault.get(
            'res.config.settings', "scb_api_key")
        scb_api_secret = IrDefault.get(
            'res.config.settings', "scb_api_secret")
        biller_id = IrDefault.get(
            'res.config.settings', "biller_id")
        if not scb_api_secret:
            return {"success": "false", "message": "Please provide SCB Api key", "data": []}
        if not scb_api_secret:
            return {"success": "false", "message": "Please provide SCB Secret key", "data": []}
        if not biller_id:
            return {"success": "false", "message": "Please provide SCB Biller Id", "data": []}
        # url = "https://api-sandbox.partners.scb/partners/sandbox/v1/oauth/token"
        url = "https://api-uat.partners.scb/partners/v1/oauth/token"

        payload = json.dumps({
            "applicationKey": scb_api_key,
            "applicationSecret": scb_api_secret
        })
        headers = {
            'Content-Type': 'application/json',
            'resourceOwnerId': scb_api_key,
            'requestUId': '5ffae525-581b-46db-939d-ae44dd9e786b',
            'accept-language': 'EN',
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        response = json.loads(response.text)
        data = response.get('data')
        order_ref = str(order_id.name.upper())
        order_ref = order_ref.replace('/', '')
        order_ref = order_ref.replace(' ', '')
        if data:
            access_token = data.get('accessToken')
            if access_token:
                # url = "https://api-sandbox.partners.scb/partners/sandbox/v1/payment/qrcode/create"
                url = "https://api-uat.partners.scb/partners/v1/payment/qrcode/create"

                payload = json.dumps({
                    "qrType": "PP",
                    "ppType": "BILLERID",
                    "ppId": biller_id,
                    "amount": str(order_id.amount_total),
                    "ref1": order_ref,
                    "ref2": order_ref,
                    "ref3": "TBI"
                })
                headers = {
                    'Content-Type': 'application/json',
                    'authorization': 'Bearer ' + access_token,
                    'resourceOwnerId': scb_api_key,
                    'requestUId': '16708412-33a9-41be-a6d2-ba4ba82584b2',
                    'accept-language': 'EN',
                }

                response = requests.request("POST", url, headers=headers, data=payload)
                response = json.loads(response.text)
                data = response.get('data')
                if data:
                    # directory = os.path.dirname(os.path.realpath(__file__))
                    # directory = directory.replace('models', '')
                    # path = directory + 'static/src/img/logo.png'
                    # Logo_link = path
                    #
                    # logo = Image.open(Logo_link)
                    # # adjust logo size
                    # basewidth = 50
                    # wpercent = (basewidth / float(logo.size[0]))
                    # hsize = int((float(logo.size[1]) * float(wpercent)))
                    # logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)

                    qr_raw_data = data.get('qrRawData')
                    qr_image = data.get('qrImage')
                    # img = Image.open(BytesIO(base64.b64decode(qr_image)))
                    # img = img.convert('RGB')
                    # pos = ((img.size[0] - logo.size[0]) // 2,
                    #        (img.size[1] - logo.size[1]) // 2)
                    # img.paste(logo, pos)
                    # buffered = BytesIO()
                    # img.save(buffered, format="JPEG")
                    # img_str = base64.b64encode(buffered.getvalue())
                    # img_str = img_str.decode("utf-8")
                    # qr_data = {'qr_raw_data': qr_raw_data, 'qr_image': img_str}
                    qr_data = {'qr_raw_data': qr_raw_data, 'qr_image': qr_image}
                    return {'success': "true",
                            'message': "Qr code generated",
                            "data": [qr_data] or []
                            }
                else:
                    return {'success': "false",
                            'message': "No response from server",
                            "data": [response]
                            }
        else:
            return {'success': "false",
                    'message': "No response from server",
                    "data": [response]
                    }

    # def build_version_check(self, build_version=None):
    #     if build_version:
    #         active_version = self.env['ir.config_parameter'].get_param('active_build_version')
    #         if active_version == build_version:
    #             return {"success": "true", "message": "App is up to date", "data": [{"current_build": active_version}]}
    #         else:
    #             return {"success": "false", "message": "App needs to be updated",
    #                     "data": [{"current_build": active_version}]}
    #     else:
    #         return {"success": "false", "message": "Cant fetch app version",
    #                 "data": []}

    # def fetch_static_qr_code(self, branch_id):
    #     branch = self.env['project.project'].search([('id', '=', branch_id)])
    #     if branch:
    #         if branch.qr_code:
    #             return {"success": "true", "message": "QR Code retrieved", "data": [{"qr_code": branch.qr_code}]}
    #         else:
    #             return {"success": "false", "message": "QR Code not added", "data": []}
    #     else:
    #         return {"success": "false", "message": "Cant find branch", "data": []}

    def redeem_coupon(self, data):
        customer = data.get('customer')
        service = data.get('service')
        branch = data.get('branch')
        plate_number = data.get('plate_number')
        if not customer:
            return {"success": "false", "message": "Please provide customer id in parameter", "data": []}
        if not service:
            return {"success": "false", "message": "Please provide service id in parameter", "data": []}
        if not branch:
            return {"success": "false", "message": "Please provide branch id in parameter", "data": []}
        if not plate_number:
            return {"success": "false", "message": "Please provide plate number id in parameter", "data": []}
        plate_number_id = self.env['car.details'].search([('id', '=', plate_number), ('partner_id', '=', customer)])
        if not plate_number_id:
            return {"success": "false", "message": "plate number not found this customer", "data": []}
        coupons = self.env['wizard.coupon'].search(
            [('partner_id', '=', customer), ('product_id.related_service_id', '=', service), ('state', '=', 'draft')])
        if coupons:
            expiring_coupons = {}
            diff = 0
            for rec in coupons:
                date_expire = datetime.strptime(str(rec.expiry_date), "%Y-%m-%d")
                date_expire = date_expire.date()
                date_diff = date_expire - date.today()
                if not expiring_coupons:
                    if date_diff.days >= 0:
                        expiring_coupons.update({'coupon': rec.id})
                        diff = date_diff.days
                else:
                    if date_diff.days >= 0 and diff > 0 and date_diff.days < diff:
                        expiring_coupons.update({'coupon': rec.id})
                        diff = date_diff.days
        else:
            return {"success": "false", "message": "no coupons found", "data": []}
        # expiring_coupon = min(expiring_dates, key=lambda x: x - date.today())
        coupon = expiring_coupons.get('coupon')
        coupon_id = self.env['wizard.coupon'].search([('id', '=', coupon)])
        # plate_number_id = self.env['car.details'].create({'name': plate_number})
        coupon_id.plate_number_id = plate_number_id.id
        coupon_id.branch_id = branch
        coupon_id.button_redeem()
        return {'success': "true" if expiring_coupons else "false",
                'message': "Coupon " + coupon_id.name + " is successfully redeemed" if expiring_coupons else "No coupons found",
                "data": expiring_coupons or []
                }

    def get_payment_result(self, data):
        order = data.get('order')
        client_order_id = data.get('client_order_id')
        # payment_method = data.get('payment_method')
        if not order:
            return {"success": "false", "message": "Please provide order id in parameter", "data": []}
        if not client_order_id:
            return {"success": "false", "message": "Please provide client order id id in parameter", "data": []}
        # if not payment_method:
        #     return {"success": "false", "message": "Please provide payment_method id in parameter", "data": []}
        if order:
            order_id = self.env['pos.order'].search([('id', '=', order), ('client_order_id', '=', client_order_id)])
            if order_id:
                statement_ids = order_id.statement_ids.ids
                if len(statement_ids) != 0 and order_id.state in ['paid', 'done', 'invoiced']:
                    return {"success": "true", "message": ("Payment done for %s" % order_id.name), "data": []}
                elif order_id.state == 'draft':
                    return {"success": "false", "message": ("Payment pending for order %s" % order_id.name),
                            "data": []}
                elif order_id.is_payment_failed:
                    return {"success": "false", "message": ("Payment failed for order %s" % order_id.name),
                            "data": []}
            else:
                return {"success": "false", "message": "Cant find order", "data": []}
        else:
            return {"success": "false", "message": "Please provide a valid order id", "data": []}
