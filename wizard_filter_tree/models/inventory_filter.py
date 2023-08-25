# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from operator import itemgetter

from odoo import models, fields, api, _




class inventory_filter(models.TransientModel):
    _name = 'inventory.filter'

    ref_from = fields.Char(string="Ref From")
    ref_to = fields.Char(string="Ref To")
    inv_from = fields.Char(string="Inv From")
    inv_to = fields.Char(string="Inv To")

    @api.multi
    def button_ok(self):
        domain = []
        action = self.env.ref('stock.action_receipt_picking_move').sudo().read()[0]
        if self.ref_from and self.ref_to:
            if self.ref_from:
                try:
                    ref_from = float(self.ref_from)
                except ValueError:
                    ref_from = self.ref_from
                    ref_from = ref_from.replace("WH/INT/", "")
                    ref_from = ref_from
                try:
                    ref_from = self.ref_from
                    ref_from = ref_from.replace("WH/OUT/", "")
                    ref_from = ref_from
                except ValueError:
                    pass
            if self.ref_to:
                try:
                    ref_to = float(self.ref_to)
                except ValueError:
                    ref_to = self.ref_to
                    ref_to = ref_to.replace("WH/INT/", "")
                    ref_to = ref_to
                try:
                    ref_to = self.ref_to
                    ref_to = ref_to.replace("WH/OUT/", "")
                    ref_to = ref_to
                except ValueError:
                    pass
            ref = self.env['stock.move'].sudo().search([('reference', '>=', self.ref_from),('reference', '<=', self.ref_to)])

            action['domain'] = ' '
            for line in ref:
                domain.append(line.reference)
            action['domain'] = [('reference', '=',domain)]
        elif self.inv_from and self.inv_to:
            if self.inv_from:
                try:
                    inv_from = float(self.inv_from)
                except ValueError:
                    inv_from = self.inv_from
                    inv_from = inv_from.replace("IV", "")
                    inv_from = inv_from
            if self.inv_to:
                try:
                    inv_to = float(self.inv_to)
                except ValueError:
                    inv_to = self.inv_to
                    inv_to = inv_to.replace("IV", "")
                    inv_to = inv_to
            ref = self.env['stock.move'].sudo().search([('invoice_stock_picking.number', '>=', self.inv_from),('invoice_stock_picking.number', '<=', self.inv_to)])
            action['domain'] = ' '
            for line in ref:
                domain.append(line.invoice_stock_picking.id)
            action['domain'] = [('invoice_stock_picking', '=', domain)]

        return action
