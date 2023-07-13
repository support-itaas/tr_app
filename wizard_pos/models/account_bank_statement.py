# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt.Ltd.(<http://www.technaureus.com/>).
from odoo import api, fields, models, _


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.multi
    def button_confirm_bank(self):
        for statement in self:
            if not statement.journal_id.wallet_journal:
                return super(AccountBankStatement, self).button_confirm_bank()

