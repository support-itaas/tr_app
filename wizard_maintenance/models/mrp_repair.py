# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date

class Mrp_repair(models.Model):
    _inherit = 'mrp.repair'

    engineer = fields.Many2one('hr.employee', string="Engineer")
    point = fields.Integer(string="Point")
    engineer1 = fields.Many2many('hr.employee', string="Engineer")


