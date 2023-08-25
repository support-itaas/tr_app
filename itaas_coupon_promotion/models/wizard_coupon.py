# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import datetime
from datetime import date, timedelta

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class WizardCoupon(models.Model):
    _inherit = 'wizard.coupon'

    is_promotion_transfer = fields.Boolean(string='Promotion Transfer')



    @api.multi
    def transfer_coupon_app(self, coupon_ids, current_partner_id, note, mobile):
        # app
        if current_partner_id:
            current_partner = self.env['res.partner'].browse(current_partner_id)
            if coupon_ids:
                coupons = self.env['wizard.coupon'].browse(coupon_ids)
            else:
                return False
            ##### case promotion transfer
            if current_partner.mobile == mobile and coupons and not coupons[0].is_promotion_transfer:
                return False
            else:
                super(WizardCoupon, self).transfer_coupon_app(coupon_ids,current_partner_id,note,mobile)
                coupons.write({'is_promotion_transfer': False})
        else:
            return False

    @api.multi
    def transfer_coupon_app_new(self, BARCODE, PARTNER_ID):
        # for app

        coupon = self.env['wizard.coupon'].search([('barcode', '=', BARCODE)])
        if coupon and BARCODE:
            if not coupon.is_promotion_transfer:
                return [{
                    'message': 'invalid_code'
                }]
            else:
                coupon.partner_id = PARTNER_ID
                coupon.is_promotion_transfer = False
                return [{
                    'message': 'success'
                }]
        else:
            return [{
                # 'message': "Coupon Doesn't Exist"
                'message': "invalid_code"
            }]