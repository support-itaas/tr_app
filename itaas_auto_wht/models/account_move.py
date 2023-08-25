# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from datetime import date, datetime
from odoo.tools import float_compare, float_is_zero

class account_move_inherit_wht(models.Model):
    _inherit = 'account.move'

    @api.multi
    def action_gen_wht(self):
        res = super(account_move_inherit_wht, self).action_gen_wht()
        for line in self.line_ids:

            if line.account_id.code == '24-01-01-03' or line.account_id.code == '24-01-01-04' and line.amount_before_tax:
                if line.wht_type == '1%':
                    wht_temp = 1
                    line.credit = round((line.amount_before_tax * wht_temp) / 100, 2)
                elif line.wht_type == '1.5%':
                    wht_temp = 1.5
                    line.credit = round((line.amount_before_tax * wht_temp) / 100, 2)
                elif line.wht_type == '2%':
                    wht_temp = 2
                    line.credit = round((line.amount_before_tax * wht_temp) / 100,2)
                elif line.wht_type == '3%':
                    wht_temp = 3
                    line.credit = round((line.amount_before_tax * wht_temp) / 100,2)
                elif line.wht_type == '5%':
                    wht_temp = 5
                    line.credit = round((line.amount_before_tax * wht_temp) / 100, 2)

                # line.credit = round((line.amount_before_tax * wht_temp) / 100,2)

        return res

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('amount_before_tax')
    def _onchange_wht_credit(self):
        print(self.amount_before_tax)
        wht_temp = 0
        if self.account_id.code == '24-01-01-03' or self.account_id.code == '24-01-01-04':
            if self.wht_type == '1%':
                wht_temp = 1
            elif self.wht_type == '1.5%':
                wht_temp = 1.5
            elif self.wht_type == '2%':
                wht_temp = 2
            elif self.wht_type == '3%':
                wht_temp = 3
            elif self.wht_type == '5%':
                wht_temp = 5
            self.credit = round((self.amount_before_tax * wht_temp) / 100)




