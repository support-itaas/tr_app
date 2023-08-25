# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd(<http://www.technaureus.com/>).

from datetime import datetime
from odoo import api, fields, models,_
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    is_create_picking_gen = fields.Boolean('Create picking', copy=False, default=True)

    @api.multi
    def create_stock_picking_gen(self):
        print('create_stock_picking_gen')
        dealer_move_lines = self.move_lines.filtered(lambda m: m.product_id.is_dealer_order_available_expenses)
        if dealer_move_lines:
            is_use = self.env['stock.location'].search([('is_use','=',True)],limit=1)
            default_cut_off = self.env['stock.picking.type'].search([('default_cut_off', '=', True)], limit=1)
            val = {
                'partner_id': self.partner_id.id,
                'location_id': self.location_dest_id.id,
                'location_dest_id': is_use.id,
                'picking_type_id': default_cut_off.id,
                'employee_id': self.employee_id.id,
                'force_date': self.force_date,
                'purchase_id': self.purchase_id.id,
                'origin': self.name,
                'is_create_picking_gen': False,
            }
            picking_id = self.env['stock.picking'].create(val)
            move_ids_done = self.env['stock.move'].browse()

            for line in dealer_move_lines:
                print('==============')
                val_move ={
                    'picking_id': picking_id.id,
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'location_id': line.location_dest_id.id,
                    'location_dest_id': is_use.id,
                    # 'lot_id': line.move_line_ids.lot_id.id,
                    # 'move_line_ids': [(6, 0, line.move_line_ids.ids)]
                }
                print('val_move :', val_move)
                move_id = self.env['stock.move'].create(val_move)
                move_ids_done += move_id

            move_ids_done._action_confirm()
            move_ids_done._action_assign()
            print ('move_ids_done:',move_ids_done)

            # print (picking_id.state)
            # picking_id.action_assign()
            if picking_id.state in ('assigned','confirmed'):
                print ('validate')

            for move in move_ids_done:
                for ml in move.move_line_ids:
                    ml.update({'qty_done': ml.product_uom_qty})
                    print('ml qty_done: ',ml.qty_done)

            print('picking_id : ',picking_id)
            print('picking_id move_lines : ',picking_id.move_lines)
            print('picking_id move_line_ids : ',picking_id.move_line_ids)
            picking_id.button_validate()

        # picking_id.action_assign()
        # val_move_line ={
        #     'picking_id': picking_id.id,
        #     'move_id': move_id.id,
        #     'location_id': line.location_id.id,
        #     'product_id': line.product_id.id,
        #     'product_uom_id':line.product_uom.id,
        #     'location_dest_id': is_use.id,
        #     'lot_id': move_id.lot_id.id,
        # }
        # self.env['stock.move.line'].create(val_move_line)

    def action_done(self):
        res = super(Picking, self).action_done()
        print("action_done :,res")
        if self.is_create_picking_gen and self.requisition_picking_id.id:
            print('get_spare_parttttttttt')
            self.create_stock_picking_gen()
        return res


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    default_cut_off = fields.Boolean(string='Default Cut Off')
