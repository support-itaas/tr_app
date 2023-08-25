from odoo import api, fields, models


class Purchase_order(models.Model):
    _inherit = 'purchase.order'

    # picking_type_id = fields.Many2one('stock.picking.type',string='Picking Type',related="operating_unit_id.picking_type_id")
    


    @api.onchange('operating_unit_id')
    def onchange_operating_unit(self):
        if self.operating_unit_id.picking_type_id:
            self.picking_type_id =  self.operating_unit_id.picking_type_id.id
        else:
            self.picking_type_id = ''




class Operating_unit_itaas(models.Model):
    _inherit = 'operating.unit'

    picking_type_id = fields.Many2one('stock.picking.type',string='Picking Type')

    show_invoice = fields.Boolean(string="Invoice")



