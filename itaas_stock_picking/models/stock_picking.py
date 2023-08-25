# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd(<http://www.technaureus.com/>).

from datetime import datetime
from odoo import api, fields, models,_
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    is_create_picking = fields.Boolean('Create picking', copy=False, default=True)

    @api.multi
    def create_stock_picking(self):
        print('***create_stock_picking')
        print('company_id : ', self.company_id.name)
        dealer_move_lines = self.move_lines.filtered(lambda m: m.product_id.is_dealer_order_available_expenses)
        print('dealer_move_lines ', dealer_move_lines)
        if dealer_move_lines:
            is_use = self.env['stock.location'].search([('is_use','=',True),('company_id','=', self.company_id.id)], limit=1)
            default_cut_off = self.env['stock.picking.type'].search([('default_cut_off', '=', True),
                                                                     ('warehouse_id.company_id','=', self.company_id.id)], limit=1)
            val = {
                'partner_id': self.partner_id.id,
                'location_id': self.location_dest_id.id,
                'location_dest_id': is_use.id,
                'picking_type_id': default_cut_off.id,
                'employee_id': self.employee_id.id,
                'force_date': self.force_date,
                'purchase_id': self.purchase_id.id,
                'origin': self.name,
                'is_create_picking': False,
                'company_id': self.company_id.id,
            }
            picking_id = self.env['stock.picking'].create(val)
            move_ids_done = self.env['stock.move'].browse()

            for line in dealer_move_lines:
                move_line_ids = []
                for move_line in line.move_line_ids:
                    val_move_line = {
                        'picking_id': picking_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': move_line.qty_done,
                        'qty_done': move_line.qty_done,
                        'product_uom_id': move_line.product_uom_id.id,
                        'location_id': line.location_dest_id.id,
                        'location_dest_id': is_use.id,
                        'lot_id': move_line.lot_id.id,
                    }
                    move_line_ids.append((0, 0, val_move_line))
                val_move = {
                    'picking_id': picking_id.id,
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'location_id': line.location_dest_id.id,
                    'location_dest_id': is_use.id,
                    'company_id': self.company_id.id,
                    'move_line_ids': move_line_ids,
                }
                print('val_move :', val_move)
                move_id = self.env['stock.move'].create(val_move)
                move_ids_done += move_id

            move_ids_done._action_confirm()
            move_ids_done._action_assign()
            print('move_ids_done :', move_ids_done)
            for move in move_ids_done:
                for line in move.move_line_ids:
                    print('product ', line.product_id)
                    print('product_uom_qty ', line.product_uom_qty)
                    print('qty_done ', line.qty_done)
                    print('lot ', line.lot_id)
                    line.update({'qty_done': line.product_uom_qty})

            print('picking_id.state :', picking_id.state)
            if picking_id.state in ('assigned'):
                print('validate')
                picking_id.button_validate()

            print('picking_id : ',picking_id.is_create_picking)
            print('picking_id move_lines : ',picking_id.move_lines)
            print('picking_id move_line_ids : ',picking_id.move_line_ids)
            print('**picking_id : ', picking_id)

    def action_done(self):
        print('Picking : ',self.name)
        print('company_id : ',self.company_id.name)
        res = super(Picking, self).action_done()
        if self.is_create_picking and self.company_id.is_create_stock_picking:
            self.create_stock_picking()
        return res

    def picking_immediate_process(self):
        print('picking_immediate_process')
        pick_to_backorder = self.env['stock.picking']
        pick_to_do = self.env['stock.picking']
        for picking in self:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(
                            _("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

            print('picking._check_backorder()')
            print(picking._check_backorder())
            if picking._check_backorder():
                pick_to_backorder |= picking
                continue
            pick_to_do |= picking
        # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
        print('PICK TO DO')
        print(pick_to_do)
        if pick_to_do:
            print('ACTION DONE')
            pick_to_do.action_done()
        if pick_to_backorder:
            return pick_to_backorder.action_generate_backorder_wizard()
        return False


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    default_cut_off = fields.Boolean(string='Default Cut Off')
