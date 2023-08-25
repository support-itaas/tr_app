# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class account_journal(models.Model):
    _inherit = "account.journal"

    relation_journal = fields.Text(string='Relation Journal')





