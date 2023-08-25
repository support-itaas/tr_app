# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Purchase_approval_matrix(models.Model):
    _name = 'purchase.approval.matrix'
    _inherit = 'mail.thread'
    _order = 'order,type,max_amount asc'

    name = fields.Char(string='Description')
    purchase_type = fields.Many2one('purchase.type', string='Purchase Type')
    type = fields.Selection([('PR','PR'),('PO','PO')],string='Type')
    max_amount = fields.Float(string='Max Approval Amount')
    group_id = fields.Many2one('res.groups', string='Approve Group')
    order = fields.Integer(string='Order')

    @api.multi
    def fix_warehouse(self):
        self.env['stock.location']._parent_store_compute()


