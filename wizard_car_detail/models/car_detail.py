# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from datetime import datetime
from datetime import timedelta
from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
import math
import random
import http.client, urllib.parse
from odoo.addons import decimal_precision as dp




class CarDetails(models.Model):
    _inherit = "car.details"
    _description = 'Adding Car Plate Number'

    brand_id = fields.Many2one('fleet.vehicle.model.brand', string='Brand')
    model_id = fields.Many2one('fleet.vehicle.model', string='Model')
    order_year = fields.Integer(string="Year")
    model_detail = fields.Char(string='Detail')
