# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    location_dest_id = fields.Many2one('stock.location', 'Destination', domain=[('usage', 'in',['internal', 'transit'])])
    department_line_id = fields.Many2one('hr.department', string='Department')

    @api.onchange('date_planned')
    def onchange_date_planned(self):
        # print("date_planned")
        self.action_set_date_planned()
        # for line in self.order_line:
        #     line.date_planned = self.date_planned

    @api.onchange('department_line_id')
    def onchange_department_line(self):
        # print("department_line_id")
        for line in self.order_line:
            line.department_id = self.department_line_id

    @api.onchange('location_dest_id')
    def onchange_location_dest(self):
        # print("location_dest_id")
        for line in self.order_line:
            line.location_dest_id = self.location_dest_id





