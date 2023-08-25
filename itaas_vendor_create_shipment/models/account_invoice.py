
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    picking_ids = fields.One2many('stock.picking', 'bill_id', string='Stock Picking')
    shipment_count = fields.Integer(string='Shipment', compute='_compute_picking_ids')

    @api.multi
    def create_shipment(self, force=False):
        print('create_shipment')
        voucher_move_lines = self.invoice_line_ids.filtered(lambda m: m.product_id.id)
        location_bill = self.operating_unit_id.picking_type_id.default_location_src_id
        location_dest_bill = self.operating_unit_id.picking_type_id.default_location_dest_id
        picking_type_bill_id = self.operating_unit_id.picking_type_id
        vals={
            'location_id': location_bill.id,
            'location_dest_id': location_dest_bill.id,
            'picking_type_id': picking_type_bill_id.id,
            'bill_id': self.id,
        }
        print('vals :',vals)
        picking_id = self.env['stock.picking'].create(vals)
        for line in voucher_move_lines:
            vals_invoice_line = {
                'picking_id': picking_id.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'product_uom_qty': line.quantity,
                'product_uom': line.uom_id.id,
                'location_id': location_bill.id,
                'location_dest_id': location_dest_bill.id,
                'remaining_qty': line.quantity,
            }
            print('vals_invoice_line :', vals_invoice_line)
            move_id = self.env['stock.move'].create(vals_invoice_line)

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.shipment_count = len(order.picking_ids)

    @api.multi
    def action_view_shipment(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action