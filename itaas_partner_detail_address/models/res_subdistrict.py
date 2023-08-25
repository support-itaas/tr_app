# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models


class ResSubDistrict(models.Model):
    _name = "res.sub.district"
    _description = "Sub District"

    district_id = fields.Many2one('res.district', string='District', required=True)
    name = fields.Char(string='Sub District Name', required=True)
    code = fields.Char(string='Sub District Code', help='The sub district code.', required=True)
