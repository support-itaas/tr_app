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
            # print ('rec.package_id.is_limit_branch',rec.package_id.is_limit_branch)
            # print('button_redeem-1',rec.order_branch_id)
            # print('button_redeem-2', branch_id)
            # if rec.package_id.is_limit_branch and rec.order_branch_id.id != branch_id and rec.purchase_date > '2022-04-01':
            #     raise UserError(_('This coupon only use the same with order branch'))
            return super(WizardCoupon, self).button_redeem(plate_id,branch_id,order_date,car_clean,barcode)



