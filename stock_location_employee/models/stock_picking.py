# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # employee_id = fields.Many2one('hr.employee', string="Employee",)

    @api.model
    def default_get(self, flds):
        result = super(StockPicking, self).default_get(flds)
        # print('default_get : ', result)
        employee_id = False
        if result.get('location_id'):
            # print('location_id')
            location_odj = self.env['stock.location'].browse(result.get('location_id'))
            employee_id = location_odj.employee_id.id or False
        elif result.get('location_dest_id'):
            # print('location_dest_id')
            location_odj = self.env['stock.location'].browse(result.get('location_dest_id'))
            employee_id = location_odj.employee_id.id or False

        if employee_id:
            result.update({'employee_id': employee_id})

        if 'force_date' not in result or not result.get('force_date'):
            result.update({'force_date': fields.Datetime.now()})
        # print('result : ',result)
        return result

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        employee_id = False
        if 'employee_id' not in vals and vals.get('location_id'):
            location_odj = self.env['stock.location'].browse(vals.get('location_id'))
            employee_id = location_odj.employee_id.id or False
        elif 'employee_id' not in vals and vals.get('location_dest_id'):
            location_odj = self.env['stock.location'].browse(vals.get('location_dest_id'))
            employee_id = location_odj.employee_id.id or False

        if employee_id:
            res.update({'employee_id': employee_id})

        return res

    @api.onchange('location_dest_id')
    def onchange_location_dest(self):
        if self.location_dest_id:
            self.employee_id = self.location_dest_id.employee_id.id
        else:
            self.employee_id = False





