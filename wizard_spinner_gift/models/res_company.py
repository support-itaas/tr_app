# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import api, fields, models
import requests
import json


class ResCompany(models.Model):
    _inherit = "res.company"

    is_live = fields.Boolean(string='Live',default=False)

