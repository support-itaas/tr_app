# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd(<http://www.technaureus.com/>).

from datetime import datetime
from odoo import api, fields, models,_
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.location"

    is_use = fields.Boolean(string='Is a Use')