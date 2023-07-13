# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models


class NewsPromotions(models.Model):
    _name = 'news.promotions'
    _description = 'News & Promotions'

    name = fields.Char('Title', required=True, help="Title")
    description = fields.Text(string="Description", required=True, help="If you use html\
                            content for answers and if you are using iframe, \
                            then set the video width as 100% and height as 250")
    sequence = fields.Integer(string="Sequence", required=True)
    image = fields.Binary("Image", attachment=True)
    type = fields.Selection([('news', 'News'), ('promotions', 'Promotions')], string='Type', default='news',
                            required=True)
