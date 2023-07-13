# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from logging import exception

from odoo import http
from odoo.models import check_method_name
from odoo.api import call_kw, Environment
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception, Response
import json
from odoo.http import Response, request
import base64
from datetime import date
from openerp.osv import osv
from odoo.tools.translate import _
from odoo.exceptions import UserError


class DataSet(http.Controller):

    def _call_kw(self, model, method, args, kwargs):
        check_method_name(method)
        return call_kw(request.env[model], method, args, kwargs)

    @http.route('/web/dataset/call_button_wizard', type='json', auth="user")
    def call_button(self, model, method, args, domain_id=None, context_id=None):
        action = self._call_kw(model, method, args, {})
        # if isinstance(action, dict) and action.get('type') != '':
        #     return clean_action(action)
        return action


class QRCode(http.Controller):

    @http.route(['/web/redeem=<string:data>'], auth='user', method='POST', type="http")
    def decode_qr_code(self, data):
        print('here entered...')
        try:
            datas = base64.b64decode(data)
            print('datas', datas)
        except Exception as e:
            # raise e
            message_id = "Error in QR Code data. " + str(e)
            return request.env['ir.ui.view'].render_template("wizard_coupon.redeem_template", {'message': message_id})
        json_data = json.loads(datas)
        if 'couponIds' not in json_data or not json_data['couponIds']:
            message_id = "Coupons Missing"
            return request.env['ir.ui.view'].render_template("wizard_coupon.redeem_template", {'message': message_id})

        names = ""
        for coupon_id in json_data['couponIds']:
            coupon = request.env['wizard.coupon'].search([('id', '=', coupon_id)])

            if not coupon:
                message_id = "Coupons Does not Exist."
                return request.env['ir.ui.view'].render_template("wizard_coupon.redeem_template",
                                                                 {'message': message_id})
            if coupon.state != 'draft':
                message_id = "Coupon " + coupon.name + " Already Redeemed."
                return request.env['ir.ui.view'].render_template("wizard_coupon.redeem_template",
                                                                 {'message': message_id})

            coupon.branch_id = json_data.get('branchId')
            coupon.plate_number_id = json_data.get('plateNumberId')

            plate_id = json_data.get('plateNumberId')
            branch_id = json_data.get('branchId')
            order_date = date.today()
            car_clean = None
            barcode = None
            print('plate_id', plate_id)
            print('branch_id', branch_id)
            print('order_date', order_date)
            print('car_clean', car_clean)
            print('barcode', barcode)

            coupon.button_redeem(plate_id,
                                 branch_id,
                                 order_date,
                                 car_clean,
                                 barcode)
            names += coupon.name + ","
        message_id = "Coupon " + names + " successfully redeemed."
        return request.env['ir.ui.view'].render_template("wizard_coupon.redeem_template", {'message': message_id})
