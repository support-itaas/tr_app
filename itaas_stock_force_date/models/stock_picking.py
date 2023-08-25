# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd(<http://www.technaureus.com/>).

from datetime import datetime
from odoo import api, fields, models,_
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    force_date = fields.Datetime(string='Force Date',
                                 states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, )

    @api.multi
    def button_validate(self):
        res = super(Picking,self).button_validate()
        if not self.force_date:
            raise UserError(_('ต้องกำหนดวันที่ในช่อง Force Date ก่อนกดตรวจสอบ'))
        return res
