
from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    relation_account = fields.Text(string='Relation Account')
