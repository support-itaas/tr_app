# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models


class HelpSupport(models.Model):
    _name = 'help.support'
    _description = 'Help & Support'

    name = fields.Char('Question', required=True, help="Question")
    answer = fields.Text(string="Answer", required=True, help="If you use html content for answers\
                                        and if you are using iframe, then set the video \
                                                              width as 100% and height as 250")
    sequence = fields.Integer(string="Sequence", required=True)
