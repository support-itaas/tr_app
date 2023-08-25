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



class WizardCoupon(models.Model):
    _inherit = 'wizard.coupon'

    signup = fields.Selection([
        ('not_signup', 'Not Signup'),
        ('mobile', 'Mobile'),
        ('gmail', 'Gmail'),
        ('facebook', 'Facebook'),
        ('apple', 'Apple'),
    ],compute='partner_sign_up',store=True)
    mobile = fields.Char(string='Mobile',compute='partner_sign_up',store=True)

    @api.depends('partner_id')
    def partner_sign_up(self):
        for coupon in self:
            if coupon.partner_id:
                coupon.signup = coupon.partner_id.signup
                coupon.mobile = coupon.partner_id.mobile
            else:
                coupon.signup = False
                coupon.mobile = False

