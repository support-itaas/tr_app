# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class res_company(models.Model):
    _inherit = 'res.company'

    is_auto_confirm_po = fields.Boolean(string='Auto Confirm PO')