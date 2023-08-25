# -*- coding: utf-8 -*-
# Copyright (C) 2020-present Itaas.


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # @api.model
    # def create(self, vals):
    #     ref = vals.get('order_type')
    #     order_type_id = self.env['purchase.order.type'].browse(ref)
    #     date_order = str(vals.get('date_order')).split(' ')
    #
    #     if order_type_id.purchase_sequence_id and not vals.get('date_order'):
    #         se_code = order_type_id.purchase_sequence_id.code
    #         if vals.get('name', 'New') == 'New':
    #             vals['name'] = self.env['ir.sequence'].next_by_code(se_code) or '/'
    #
    #     if vals.get('date_order'):
    #         if vals.get('name', 'New') == 'New':
    #             se_code = order_type_id.purchase_sequence_id.code
    #             vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=date_order[0]).next_by_code(se_code) or '/'
    #     else:
    #         raise UserError(_('You don\'t  sequence. And try again.'))
    #
    #     defaults = self.default_get(['name', 'picking_type_id'])
    #     if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
    #         vals['name'] = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id'))).sequence_id.next_by_id()
    #
    #     return super(StockPicking, self).create(vals)

    @api.model
    def create(self, vals):
        print("create StockPicking")
        print("vals : " + str(vals))
        defaults = self.default_get(['name', 'picking_type_id'])

        if vals.get('date') and defaults.get('name', '/') == '/' and vals.get('picking_type_id',defaults.get('picking_type_id')):
            date_time = vals.get('date')
            date_planned = vals.get('date_planned')

            if type(date_time) == 'datetime.date':
                date_time = date_time.strftime("%Y-%m-%d %H:%M:%S")
            date = str(date_time).split(' ')
            date = date[0]

            if date_planned:
                date_planned = str(date_planned).split(' ')
                date_planned = date_planned[0]
                date = date_planned

            print("date : " + str(date))
            print("date_planned : " + str(date_planned))
            picking_type_id = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
            sequence = picking_type_id.sequence_id
            print(picking_type_id)
            vals['name'] = sequence.with_context(ir_sequence_date=date).next_by_id() or '/'

        return super(StockPicking, self).create(vals)


