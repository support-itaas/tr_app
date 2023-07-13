# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    social_instagram = fields.Char(string="Instagram Account")
    social_line = fields.Char(string="Line Account")
