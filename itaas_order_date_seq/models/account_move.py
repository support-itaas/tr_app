# -*- coding: utf-8 -*-
# Copyright (C) 2020-present Itaas.


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Account_Move_button(models.Model):
    _inherit = 'account.move'

    @api.multi
    def gen_reference(self):
        print('gen_reference')
        for line in self.line_ids.filtered(lambda m: m.wht_type):
            print('line:',line)
            if line.wht_personal_company == 'personal':
                line.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code('wht3.no') or '/'
            elif line.wht_personal_company == 'company':
                line.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code(
                    'wht53.no') or '/'


        # move_ids =  self.env['account.move'].search([('wht_reference','!=','')])
        # for move_id in move_ids:
        #     for line_id in move_id.line_ids.filtered(lambda m: m.wht_type):
        #         print('line_id:',line_id)
        #         line_id.wht_reference = move_id.wht_reference







