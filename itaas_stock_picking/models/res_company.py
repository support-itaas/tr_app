# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd(<http://www.technaureus.com/>).

from datetime import datetime
from odoo import api, fields, models,_
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    is_create_stock_picking = fields.Boolean(string='Is a Create Stock Picking')