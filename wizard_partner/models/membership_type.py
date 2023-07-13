# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models


class MembershipType(models.Model):
    _name = 'membership.type'
    _description = 'Showing Membership Type'

    name = fields.Char(required=True)
    color = fields.Char(required=True)
    thai_name = fields.Char(required=True)
    sequence = fields.Integer(string="Sequence", required=True, default=1)
    point_from = fields.Integer(string="Point From")
    point_to = fields.Integer(string="Point To")
    amount_from = fields.Integer(string="Amount From")
    amount_to = fields.Integer(string="Amount To")
