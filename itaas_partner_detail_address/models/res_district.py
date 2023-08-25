# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models


class ResDistrict(models.Model):
    _name = "res.district"
    _description = "District"

    state_id = fields.Many2one('res.country.state', string='State', required=True)
    name = fields.Char(string='District Name', required=True)
    code = fields.Char(string='District Code', help='The district code.', required=True)
