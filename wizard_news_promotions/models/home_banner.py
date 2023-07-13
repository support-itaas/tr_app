# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models, api
from odoo.exceptions import UserError


class HomeBanner(models.Model):
    _name = 'home.banner'
    _description = 'Home Banner'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", required=True)
    image = fields.Binary(required=True)
    active = fields.Boolean(default=True)
    news_promo_id = fields.Many2one('news.promotions', string="News & Promotions Link")

    @api.model
    def create(self, vals):
        if vals.get('sequence') < 1:
            raise UserError("Sequence number should be greater than Zero.")
        return super(HomeBanner, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(HomeBanner, self).write(vals)
        if self.sequence < 1:
            raise UserError("Sequence number should be greater than Zero.")
        return res
