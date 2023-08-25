# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.modules.module import get_module_resource
import base64
import datetime
from datetime import date
from odoo.exceptions import UserError

class Stock_Picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        res = super(Stock_Picking, self).button_validate()
        print(self.picking_type_code)
        print(self.purchase_id)
        if self.picking_type_code == 'incoming' and self.purchase_id:
            eval_ids = self.env['supplier.evaluation.line'].search([('picking_id', '=', self.id),
                                                                    ('partner_id', '=', self.partner_id.id)],limit=1)
            print('eval_ids ',eval_ids)
            if not eval_ids and not self.is_reverse:
                raise UserError(_('ต้องทำการประเมินก่อนกด Validate'))

            # if not self.partner_id.main_company:
            #     check_pass_fail = self.env['supplier.evaluation.line'].search([('picking_id', '=', self.id),
            #                                                                    ('pass_fail', '!=', False),
            #                                                                    ('partner_id', '=', self.partner_id.id)],limit=1)
            #     if not check_pass_fail:
            #         raise UserError(_('ต้องทำการประเมิน Pass/Fail ก่อนกด Validate'))

        return res
