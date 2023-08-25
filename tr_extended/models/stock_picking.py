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
    def create_evaluation_in_vendors(self):

        self.function_create_evaluation_in_vendors()

        action = self.env.ref('base.action_partner_supplier_form')
        result = action.read()[0]

        result['context'] = {}

        res = self.env.ref('base.view_partner_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = self.partner_id.id

        return result

    @api.multi
    def function_create_evaluation_in_vendors(self):
        today = date.today()
        type_ids = self.env['evaluation.type'].search([])
        eval_ids = self.env['supplier.evaluation.line'].search([('picking_id','=',self.id)])
        print (eval_ids)
        if not eval_ids:
            print ('---------------1')
            for type in type_ids:
                eval_s = {
                    'date': today,
                    'name': type.id,
                    'po_id': self.purchase_id.id,
                    'picking_id': self.id,
                    'partner_id': self.partner_id.id,
                    'pass_fail': True,
                }
                self.partner_id.evaluation_line_ids.create(eval_s)
        else:
            print ('--------------2')
            eval_ids.unlink()
            for type in type_ids:
                eval_s = {
                    'date': today,
                    'name': type.id,
                    'po_id': self.purchase_id.id,
                    'picking_id': self.id,
                    'partner_id': self.partner_id.id,
                }
                self.partner_id.evaluation_line_ids.create(eval_s)

    # @api.multi
    # def button_validate(self):
    #     res = super(Stock_Picking, self).button_validate()
    #     print(self.picking_type_code)
    #     print(self.purchase_id)
    #     if self.picking_type_code == 'incoming' and self.purchase_id:
    #         eval_ids = self.env['supplier.evaluation.line'].search([('picking_id', '=', self.id),
    #                                                                 ('partner_id', '=', self.partner_id.id)],limit=1)
    #         print('eval_ids ',eval_ids)
    #         if not eval_ids and not self.is_reverse:
    #             raise UserError(_('ต้องทำการประเมินก่อนกด Validate'))
    #
    #         # check_pass_fail = self.env['supplier.evaluation.line'].search([('picking_id', '=', self.id),
    #         #                                                          ('pass_fail', '!=', False),
    #         #                                                          ('partner_id', '=', self.partner_id.id)],limit=1)
    #         # if not check_pass_fail:
    #         #     raise UserError(_('ต้องทำการประเมิน Pass/Fail ก่อนกด Validate'))
    #
    #     return res
