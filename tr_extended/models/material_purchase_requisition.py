# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class material_purchase_requisition(models.Model):
    _inherit = "material.purchase.requisition"

    mo_id = fields.Many2one('mrp.production', string='Mo')


    @api.onchange('mo_id')
    def onchange_mo_id(self):
        print ('onchange_mo_id')
        if self.mo_id:
            print('onchange_mo_id1')
            # self.mo_id.
            line_list = []
            for mo in self.mo_id.move_raw_ids:
                vals = {
                    'product_id': mo.product_id.id,
                    'description': mo.product_id.name,
                    'qty': mo.product_uom_qty,
                    'uom_id': mo.product_uom.id,
                }
                line_list.append((0, 0, vals))
            print (line_list)
            self.update({'requisition_line_ids': line_list})


