# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import fields, models


class SCBLog(models.Model):
    _name = 'scb.log'
    _description = 'SCB Log'
    _order = 'id desc'

    name = fields.Char(string='Transaction ID')
    scb_data = fields.Text(string='Data')
