# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import datetime
from datetime import date, timedelta

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

import math
import re



class pos_order_line(models.Model):
    _inherit = 'pos.order.line'

    package_id = fields.Many2one('wizard.coupon.pack',string='Package ID')

    def is_create(self):
        result = super(pos_order_line, self).is_create()
        print ('--is_create order line')

        for line in self:
            if line.package_id:
                print ('--Update coupon')
                line.update_coupon(line.package_id)
                result = False
        return result

    def update_coupon(self,package_id):
        print ('-update_coupon-')
        coupon_ids = self.env['wizard.coupon'].search([('coupon_running','=',package_id.name)])
        print (coupon_ids)
        for line in self:
            for coupon in coupon_ids:
                coupon.update({'partner_id':line.order_id.partner_id.id})
                package_id.update({'state':'sold'})

# class pos_order(models.Model):
#     _inherit = 'pos.order'
#
#     @api.multi
#     def create_coupons(self):