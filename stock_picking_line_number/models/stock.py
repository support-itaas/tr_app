# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    number = fields.Integer()


class StockMove(models.Model):
    _inherit = 'stock.move'

    number = fields.Integer(compute="_compute_number")

    @api.depends('sequence', 'product_id')
    def _compute_number(self):
        print('_compute_number')
        for picking_id in self.mapped('picking_id'):
            number = 1
            for line in picking_id.move_lines:
                line.number = number
                number += 1

    # @api.depends('sequence', 'product_id')
    # def _compute_number(self):
    #     # picking_id, sequence, id
    #     for invoice in self.mapped('product_id').sorted(lambda x: x.sequence and x.id):
    #         number = 1
    #         for line in invoice:
    #             line.number = number
    #             number += 1


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_number_line = fields.Boolean('xxxx')

    # @api.depends('move_lines', 'move_lines.sequence',)
    # def get_number(self):
    #     print('get_number : ',)
    #     for obj in self:
    #         number = 1
    #         for sm in obj.move_lines.sorted(lambda x: x.sequence):
    #             # **
    #             sm.number = number
    #             number += 1
    #         obj.is_number_line = True

