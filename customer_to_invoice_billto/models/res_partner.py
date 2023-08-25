# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_is_zero


class res_partner(models.Model):
    _inherit = 'res.partner'

    bill_to_id = fields.Many2one('res.partner', string='Bill to')