
from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_cost = fields.Boolean('Is Cost')
    is_expense = fields.Boolean('Is Expense')
    is_use = fields.Boolean('Is Use')


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    is_special =  fields.Boolean('Is Special')