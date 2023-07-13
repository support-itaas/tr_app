# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.
from datetime import timedelta, datetime

from odoo import api, fields, models, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    client_order_id = fields.Char(string='Client Order Key')
    expire_on = fields.Datetime(string='Expire On')
    is_payment_failed = fields.Boolean(default=False)

    @api.model
    def create(self, vals):
        res = super(PosOrder, self).create(vals)
        res.expire_on = datetime.now() + timedelta(hours=1)
        return res
