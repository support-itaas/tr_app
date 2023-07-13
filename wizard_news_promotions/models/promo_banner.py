# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models


class PromoBanner(models.Model):
    _name = 'promo.banner'
    _description = 'Promo Banner'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", required=True)
    image = fields.Binary("Photo", required=True)
    active = fields.Boolean(default=True)
    news_promo_id = fields.Many2one('news.promotions', string="News & Promotions Link")
