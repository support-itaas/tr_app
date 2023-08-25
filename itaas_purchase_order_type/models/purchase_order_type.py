# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).
from odoo import models, fields


class PurchaseOrderType(models.Model):
    _name = 'purchase.order.type'
    _description = 'Purchase Order Type'
    _inherit = ['mail.thread']

    name = fields.Char(required=True)
    active = fields.Boolean('Active', default=True, track_visibility='onchange')
    incoterm_id = fields.Many2one('stock.incoterms', 'Incoterm')
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', domain="[('code', '=', 'incoming')]")
    po_return = fields.Boolean('Return PO')
    vendor_bill_journal_id = fields.Many2one('account.journal', 'Vendor Bill Journal')
    purchase_sequence_id = fields.Many2one('ir.sequence', 'Purchase Sequence')
