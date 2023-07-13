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

    @api.multi
    def button_redeem(self, plate_id=None, branch_id=None, order_date=None, car_clean=None, barcode=None):
        for rec in self:
            # print ('button_redeem')
            if rec.product_id.is_limit_branch and rec.order_branch_id.id != branch_id:
                raise UserError(_('This coupon only use the same with order branch'))
            super(WizardCoupon, self).button_redeem(plate_id,branch_id,order_date,car_clean,barcode)



