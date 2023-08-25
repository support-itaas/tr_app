# -*- coding: utf-8 -*-
from odoo import models, fields, api, _





class StockPickinginherit(models.Model):
    _inherit = "stock.picking"


    invoice_id = fields.Many2one('account.invoice',string="Invoice",compute='_compute_invoice_id')
    invoice_id1 = fields.Char(string="Invoice" ,compute='_compute_invoice_id')
    tax_invoice_date = fields.Date(string='Tax invoice Date',related='invoice_id.date_invoice')

    @api.depends('sale_id','sale_id.invoice_ids')
    def _compute_invoice_id(self):
        for picking in self:
            if picking.sale_id.invoice_ids:
                invoice_id = picking.sale_id.invoice_ids[0]
                picking.invoice_id1 = invoice_id.number
                picking.invoice_id = invoice_id



    ######################## USE TEMPORARY, one time #########3
    ##########JA - 25/06/2020 #######3
    @api.multi
    def update_vendor_price_list(self):
        purchase_ids = self.env['purchase.order'].search([('state','in',('purchase','done'))])
        for purchase in purchase_ids:
            purchase._add_supplier_to_product()
            # print (purchase.name)
