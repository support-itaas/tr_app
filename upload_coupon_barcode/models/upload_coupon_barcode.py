# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import datetime
from datetime import date, timedelta

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

from datetime import datetime, timedelta, date
import pytz
from datetime import datetime
import xlrd
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
import base64

def strToDate(dt):
    new_date = dt.split('/')
    # print (new_date)
    # print (new_date[0])
    # print(int(new_date[0]))
    # print(new_date[1])
    # print(int(new_date[0]))
    # print(new_date[2])
    return date(int(new_date[2]), int(new_date[1]), int(new_date[0]))
    # return date(2022, 5, 3)

class UploadCouponBarcode(models.Model):
    _name = 'upload.coupon.barcode'
    _description = 'Upload Coupon'

    name = fields.Char('Name File')
    upload_file = fields.Binary('File Upload')
    upload_line_ids = fields.One2many('upload.coupon.line','upload_id', string='Upload Line')

    @api.multi
    def upload_barcode(self):
        for line in self.upload_line_ids:
            if not line.coupon and line.barcode:
                coupon_id = self.env['wizard.coupon'].search([('barcode','=',line.barcode),('state', '=', 'draft')],limit=1)
                if coupon_id:
                    if line.partner_id:
                        partner_id = line.partner_id
                    else:
                        partner_id = self.env['res.partner'].search([('mobile', '=', line.mobile)], limit=1)
                        if not partner_id:
                            partner_id = self.env['res.partner'].search([('name', '=', line.partner_name)], limit=1)

                    if partner_id:
                        coupon_id.update({'partner_id': partner_id.id})
                        coupon_id.update({'expiry_date': line.expire_date})
                        line.update({'coupon': coupon_id.id})
                    else:
                        line.update({'note':'ไม่เจอลูกค้า'})
                else:
                    # line.update({'note': 'ไม่เจอ barcode'})
                    # ('order_branch_id', '=', line.branch_id.id)
                    coupon_id = self.env['wizard.coupon'].sudo().search([('order_branch_id', '=', line.branch_id.id),('partner_id', 'in', [105714,105768,107683]),('barcode','=', False),('product_id', '=', line.product_id.id),('state', '=', 'draft')], limit=1)
                    # print (coupon_id)
                    if coupon_id:
                        partner_id = self.env['res.partner'].search([('mobile', '=', line.mobile)], limit=1)
                        if not partner_id:
                            partner_id = self.env['res.partner'].search([('name', '=', line.partner_name)], limit=1)

                        if partner_id:
                            coupon_id.update({'partner_id': partner_id.id})
                            coupon_id.update({'expiry_date': line.expire_date})
                            coupon_id.update({'barcode': line.barcode})
                            line.update({'coupon': coupon_id.id})
                            line.update({'note': ''})
                        else:
                            line.update({'note': 'ไม่เจอลูกค้า'})
                    else:
                        line.update({'note': 'ไม่เจอ คูปอง'})



class uploadcouponline(models.Model):
    _name = 'upload.coupon.line'

    barcode = fields.Char(string='Barcode')
    expire_date = fields.Date(string='Expire Date')
    partner_name = fields.Char(string='Customer')
    mobile = fields.Char(string='Mobile')
    product = fields.Char(string='Product')
    coupon = fields.Many2one('wizard.coupon', string='Coupon')
    partner_id = fields.Many2one('res.partner', string='Partner')
    product_id = fields.Many2one('product.product', string='Product')
    upload_id = fields.Many2one('upload.coupon.barcode', string='Upload')
    branch_id = fields.Many2one('project.project',string='Branch')
    note = fields.Char(string='Note')