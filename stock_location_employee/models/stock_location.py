# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date

class StockLocation(models.Model):
    _inherit = 'stock.location'

    employee_id = fields.Many2one('hr.employee', string="Employee")




