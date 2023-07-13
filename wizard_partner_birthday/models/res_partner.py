# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from datetime import datetime,date
from datetime import timedelta
import calendar

from odoo import fields, models, api, _
from odoo.exceptions import UserError

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class ResPartner(models.Model):
    _inherit = 'res.partner'


    birth_date_month = fields.Char(string='Birth Date Month',compute='_get_birth_date_month')

    @api.multi
    @api.depends('birth_date')
    def _get_birth_date_month(self):
        for rec in self:
            # task = self.env['project.task'].search([('partner_id', '=', rec.id)], order='date_deadline desc', limit=1)
            if rec.birth_date:
                rec.birth_date_month = calendar.month_name[strToDate(rec.birth_date).month]

