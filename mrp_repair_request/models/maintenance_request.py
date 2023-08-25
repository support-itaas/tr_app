# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date

class MaintenanceRequest(models.Model):
    _inherit ="maintenance.request"

    repair_ids = fields.One2many('mrp.repair', 'request_id', string='Repair Line')
    count_repair = fields.Integer('Count Repair', compute='compute_count_repair')

    def compute_count_repair(self):
        for odj in self:
            if odj.repair_ids:
                count_repair = len(odj.repair_ids)
                odj.update({'count_repair':count_repair})

    @api.multi
    def action_repair_request(self):
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        if warehouse:
            location_id = warehouse.lot_stock_id
        val = {
            'request_id': self.id,
            'equipment_id': self.equipment_id.id,
            'operating_unit_id': self.operating_unit_id.id,
            'employee_id': self.employee_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_id.id,
        }
        self.env['mrp.repair'].create(val)

    @api.multi
    def action_open_repair_ids(self):
        action = self.env.ref('mrp_repair.action_repair_order_tree').sudo().read()[0]
        repair_ids = self.repair_ids
        if len(repair_ids) > 1:
            action['domain'] = [('id', 'in', repair_ids.ids)]
        elif repair_ids:
            action['views'] = [(self.env.ref('mrp_repair.view_repair_order_form').id, 'form')]
            action['res_id'] = self.repair_ids.id
        return action