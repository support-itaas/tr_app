# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare

class MrpRepair(models.Model):
    _inherit = "mrp.repair"

    employee_id = fields.Many2one('hr.employee', string='Employee')
    equipment_id = fields.Many2one('maintenance.equipment', string='Repair For Equipment')
    request_id = fields.Many2one('maintenance.request', string='Repair For Request')

    # remove required
    product_id = fields.Many2one(
        'product.product', string='Product to Repair',
        readonly=True, required=False, states={'draft': [('readonly', False)]})
    product_qty = fields.Float(
        'Product Quantity',
        default=1.0, digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, required=False, states={'draft': [('readonly', False)]})
    product_uom = fields.Many2one(
        'product.uom', 'Product Unit of Measure',
        readonly=True, required=False, states={'draft': [('readonly', False)]})

    def action_validate(self):
        self.ensure_one()
        if self.equipment_id:
            return self.action_repair_confirm()
        else:
            return super(MrpRepair, self).action_validate()

    @api.onchange('request_id')
    def onchange_request_id(self):
        if self.request_id:
            self.equipment_id = self.request_id.equipment_id.id
            self.product_id = False
            self.product_uom = False
        else:
            self.equipment_id = False
            self.product_id = False
            self.product_uom = False

    # @api.multi
    # def action_repair_end(self):
    #     """ Writes repair order state to 'To be invoiced' if invoice method is
    #     After repair else state is set to 'Ready'.
    #     @return: True
    #     """
    #     if self.filtered(lambda repair: repair.state != 'under_repair'):
    #         raise UserError(_("Repair must be under repair in order to end reparation."))
    #     for repair in self:
    #         repair.write({'repaired': True})
    #         vals = {'state': 'done'}
    #         vals['move_id'] = repair.action_repair_done().get(repair.id)
    #         if not repair.invoiced and repair.invoice_method == 'after_repair':
    #             vals['state'] = '2binvoiced'
    #         repair.write(vals)
    #     return True

    @api.multi
    def action_repair_end(self):
        # print('action_repair_end')
        if not self.product_id and not self.operations:
            for repair in self:
                repair.write({'repaired': True})
                vals = {'state': 'done'}
                if not repair.invoiced and repair.invoice_method == 'after_repair':
                    vals['state'] = '2binvoiced'
                repair.write(vals)
        else:
            return super(MrpRepair, self).action_repair_end()

    @api.multi
    def action_repair_done(self):
        """ Creates stock move for operation and stock move for final product of repair order.
        @return: Move ids of final products

        """
        # print('def action_repair_done ทับfuction เดิมจากaddon')
        if self.product_id or self.operations:
            if self.filtered(lambda repair: not repair.repaired):
                raise UserError(_("Repair must be repaired in order to make the product moves."))
            res = {}
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            Move = self.env['stock.move']
            for repair in self:
                # Try to create move with the appropriate owner
                owner_id = False
                available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id, repair.location_id, repair.lot_id, owner_id=repair.partner_id, strict=True)
                if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                    owner_id = repair.partner_id.id

                moves = self.env['stock.move']
                for operation in repair.operations:
                    move = Move.create({
                        'name': repair.name,
                        'product_id': operation.product_id.id,
                        'product_uom_qty': operation.product_uom_qty,
                        'product_uom': operation.product_uom.id,
                        'partner_id': repair.address_id.id,
                        'location_id': operation.location_id.id,
                        'location_dest_id': operation.location_dest_id.id,
                        'move_line_ids': [(0, 0, {'product_id': operation.product_id.id,
                                                  'lot_id': operation.lot_id.id,
                                                  'product_uom_qty': 0,  # bypass reservation here
                                                  'product_uom_id': operation.product_uom.id,
                                                  'qty_done': operation.product_uom_qty,
                                                  'package_id': False,
                                                  'result_package_id': False,
                                                  'owner_id': owner_id,
                                                  'location_id': operation.location_id.id, #TODO: owner stuff
                                                  'location_dest_id': operation.location_dest_id.id,})],
                        'repair_id': repair.id,
                        'origin': repair.name,
                    })
                    moves |= move
                    operation.write({'move_id': move.id, 'state': 'done'})
                if repair.product_id:
                    move = Move.create({
                        'name': repair.name,
                        'product_id': repair.product_id.id,
                        'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                        'product_uom_qty': repair.product_qty,
                        'partner_id': repair.address_id.id,
                        'location_id': repair.location_id.id,
                        'location_dest_id': repair.location_dest_id.id,
                        'move_line_ids': [(0, 0, {'product_id': repair.product_id.id,
                                                  'lot_id': repair.lot_id.id,
                                                  'product_uom_qty': 0,  # bypass reservation here
                                                  'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                                                  'qty_done': repair.product_qty,
                                                  'package_id': False,
                                                  'result_package_id': False,
                                                  'owner_id': owner_id,
                                                  'location_id': repair.location_id.id, #TODO: owner stuff
                                                  'location_dest_id': repair.location_dest_id.id,})],
                        'repair_id': repair.id,
                        'origin': repair.name,
                    })
                consumed_lines = moves.mapped('move_line_ids')
                produced_lines = move.move_line_ids
                moves |= move
                moves._action_done()
                produced_lines.write({'consume_line_ids': [(6, 0, consumed_lines.ids)]})
                res[repair.id] = move.id

            return res
        else:
            return False






