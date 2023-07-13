# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models


class ResCountry(models.Model):
    _inherit = 'res.country'

    available_app = fields.Boolean(string="Available In App", default=False)
