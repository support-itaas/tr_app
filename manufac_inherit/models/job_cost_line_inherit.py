# -*- coding: utf-8 -*-

from odoo import api, fields, models


class mrp_job_cost_line(models.Model):
    _inherit = 'mrp.job.cost.line'

    min_to_hour = fields.Float('Hours', compute='depend_min_to_hours', store=True)

    @api.depends('minute_qty', 'product_qty')
    def depend_min_to_hours(self):
        for i in self:
            i.min_to_hour = (i.product_qty * i.minute_qty) / 60





