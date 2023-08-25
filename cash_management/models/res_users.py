# -*- coding: utf-8 -*-

from odoo import api, fields, models

class res_users(models.Model):
    _inherit = 'res.users'

    cash_management_journal_id = fields.Many2one('account.journal',string='Default Cash Journal')
    analytic_account_id = fields.Many2one('account.analytic.account', string='สาขา')







    
