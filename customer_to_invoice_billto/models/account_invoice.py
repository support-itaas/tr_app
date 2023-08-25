# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_is_zero


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(account_invoice,self)._onchange_partner_id()
        if self.partner_id and self.partner_id.bill_to_id:
            self.bill_to_id = self.partner_id.bill_to_id
        return res