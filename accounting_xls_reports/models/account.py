# -*- coding: utf-8 -*-

from odoo import fields, api, models
from odoo.tools.translate import _

class account_report_view(models.Model):

    _name = "account.report.view"
    _description = "To generate accounting reports"

    file_stream = fields.Binary(string='File Stream')
    name = fields.Char(string="File Name")
               

