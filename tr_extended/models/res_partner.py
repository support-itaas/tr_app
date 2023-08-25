# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.modules.module import get_module_resource
import base64

class res_partner(models.Model):
    _inherit = 'res.partner'

    evaluation_line_ids = fields.One2many('supplier.evaluation.line','partner_id',string='Evaluation')


class supplier_evaluation_line(models.Model):
    _name = 'supplier.evaluation.line'
    _inherit = 'mail.thread'

    name = fields.Many2one('evaluation.type', string='Type',required=True)
    date = fields.Date(string='Date',required=True)
    description = fields.Char(string='Description')
    po_id = fields.Many2one('purchase.order',string='PO',required=True)
    picking_id = fields.Many2one('stock.picking',string='Picking',required=True)
    pass_fail = fields.Boolean(string='Pass/Fail')
    partner_id = fields.Many2one('res.partner',string='Partner',required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    is_return = fields.Boolean('Return')


class evaluation_type(models.Model):
    _name = 'evaluation.type'

    name = fields.Char(string='Name')

