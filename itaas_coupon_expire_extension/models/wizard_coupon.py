# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from operator import itemgetter
from io import BytesIO
from odoo import models, fields, api, _
from datetime import datetime,date
import xlwt
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar
import requests
import json
from datetime import date, timedelta

import math
import re


def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))



class WizardCoupon(models.Model):
    _inherit = 'wizard.coupon'

    # def coupon_expire_extension(self):
    #     print (x)


class WizardCoupon(models.Model):
    _name = 'wizard.coupon.extension.log'

    name = fields.Many2one('wizard.coupon',string='Coupon')
    old_coupon = fields.Many2one('wizard.coupon',string='Old Coupon')
    partner_id = fields.Many2one('res.partner',string='Customer')
    product_id = fields.Many2one('product.product', string='Coupon Type')
    old_expire = fields.Date(string='Old Expire Date')
    new_expire = fields.Date(string='New Expire Date')
    order_branch_id = fields.Many2one('project.project',string='Order Branch')
    type = fields.Selection([('extend','ต่ออายุคุปองเดิม'),('new','ต่ออายุออกคูปองใหม่')],string='ประเภทการต่ออายุ')
    extend_reason = fields.Many2one('coupon.extend.reason',string='เหตุผลการต่ออายุ')

class WizardCouponExpireExtention(models.TransientModel):
    _name = 'wizard.coupon.expire.extension'

    new_expire_date = fields.Date(string='New Expire Date')
    type = fields.Selection([('e-coupon', 'E-Coupon'), ('paper', 'Paper')])
    order_branch_id = fields.Many2one('project.project', string="Purchase At")
    partner_id = fields.Many2one('res.partner', string='Customer')
    extend_reason = fields.Many2one('coupon.extend.reason', string='เหตุผลการต่ออายุ')

    def coupon_expire_extend(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        # for record in self.env['wizard.coupon'].browse(active_ids):
        #     record.session_id  = record.order_id.session_id

        for record in self.env['wizard.coupon'].browse(active_ids).filtered(lambda c: c.state in ['draft', 'expire']):
            # if record.move_id:
            new_coupon = record.with_context(allow_copy=True).copy()
            val_update = {
                'order_id': False,
                'session_id': False,
                'amount': 0,
                'redeem_date': False,
                'branch_id': False,
                'source_branch_amount': 0.00,
                'destination_branch_amount': 0.00,
                'expiry_date': self.new_expire_date,
                'redeem_date': False,
                'move_id': False,
                'branch_id':False,
                'state': 'draft',
                'note': 'Original Coupon ' + str(record.name)
            }
            if self.type:
                val_update['type'] = self.type
            if self.order_branch_id:
                val_update['order_branch_id'] = self.order_branch_id.id
            if self.partner_id:
                val_update['partner_id'] = self.partner_id.id

            new_coupon.update(val_update)

            val = {
                'name': new_coupon.id,
                'old_coupon': record.id,
                'product_id': record.product_id.id,
                'partner_id': record.partner_id.id,
                'old_expire': record.expiry_date,
                'new_expire': self.new_expire_date,
                'extend_reason': self.extend_reason.id,
                'order_branch_id': record.order_branch_id.id,
                'type': 'new',
            }
            self.env['wizard.coupon.extension.log'].create(val)
            record.write({'state':'expire'})
            # else:
            #
            #     val = {
            #         'name': record.id,
            #         'old_coupon': record.id,
            #         'product_id':record.product_id.id,
            #         'partner_id': record.partner_id.id,
            #         'old_expire': record.expiry_date,
            #         'new_expire': self.new_expire_date,
            #         'order_branch_id': record.order_branch_id.id,
            #         'type': 'extend',
            #     }
            #     self.env['wizard.coupon.extension.log'].create(val)
            #
            #     record.update({'expiry_date': self.new_expire_date})
            #     record.update({'state': 'draft'})
            #     record.update({'redeem_date': False})
            #     record.update({'branch_id': False})





class coupon_extend_reason(models.Model):
    _name = 'coupon.extend.reason'

    name = fields.Char(string='เหตุผลการต่ออายุ')

