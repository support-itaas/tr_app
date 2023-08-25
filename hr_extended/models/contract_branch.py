# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import datetime

class contract_branch(models.Model):
    _name = 'contract.branch'

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)











