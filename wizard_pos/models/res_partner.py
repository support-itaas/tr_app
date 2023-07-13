# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create_from_ui(self, partner):
        car_ids = partner.pop('car_ids', False)
        partner_id = super(ResPartner, self).create_from_ui(partner)
        if car_ids:
            car_ids = eval(car_ids)
            self.browse(partner_id).write({'car_ids': car_ids})
        return partner_id
