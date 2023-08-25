# -*- coding: utf-8 -*-
from openerp import fields, api, models
from bahttext import bahttext

class ResBank_inherit(models.Model):
    # _name = "res.bank.in"
    _inherit = "res.bank"

    layout_image1_top = fields.Integer('top', default=80)
    layout_image1_left = fields.Integer('left', default=30)
    layout_image1_height = fields.Integer('height', default=60)
    layout_image1_width = fields.Integer('width', default=120)
    layout_image1_show = fields.Boolean('show', default=True)

    layout_image2_top = fields.Integer('top', default=70)
    layout_image2_right = fields.Integer('right', default=20)
    layout_image2_height = fields.Integer('height', default=60)
    layout_image2_width = fields.Integer('width', default=120)
    layout_image2_show = fields.Boolean('show', default=True)


    layout_name_top = fields.Integer('top',default=87)
    layout_name_left = fields.Integer('left',default=140)
    layout_name_show = fields.Boolean('show',default=True)

    layout_amount_top = fields.Integer('top', default=160)
    layout_amount_left = fields.Integer('left', default=515)
    layout_amount_show = fields.Boolean('show', default=True)

    layout_baht_top = fields.Integer('top', default=125)
    layout_baht_left = fields.Integer('left', default=150)
    layout_baht_show = fields.Boolean('show',default=True)

    layout_date_top = fields.Integer('top', default=20)
    layout_date_left = fields.Integer('left', default=600)
    layout_date_show = fields.Boolean('show',default=True)

    layout_partner_top = fields.Integer('top', default=87)
    layout_partner_left = fields.Integer('left', default=140)
    layout_partner_show = fields.Boolean('show',default=False)
