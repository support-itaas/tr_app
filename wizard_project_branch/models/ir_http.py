# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(Http, self).session_info()
        if result['company_id']:
            company_currency = self.env['res.company'].browse(result['company_id']).currency_id
            result['currency_id'] = self.env['res.currency'].search_read([('id','=',company_currency.id)],['name'])
        return result