# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class project_task(models.Model):
    _inherit = 'project.task'

    session_id = fields.Many2one('pos.session',string='Session')
    count_type_paper = fields.Float(string='Coupon Paper', compute='_compute_check_type')
    count_type_e_coupon = fields.Float(string='E-coupon', compute='_compute_check_type')

    @api.one
    @api.depends('coupon_id.type')
    def _compute_check_type(self):
        for obj in self:
            if obj.coupon_id:
                for coupon in obj.coupon_id:
                    if coupon.type == 'e-coupon':
                        obj.count_type_paper = 0.00
                        obj.count_type_e_coupon = 1.00
                    elif coupon.type == 'paper':
                        obj.count_type_paper = 1.00
                        obj.count_type_e_coupon = 0.00
                    else:
                        obj.count_type_paper = 0.00
                        obj.count_type_e_coupon = 0.00



