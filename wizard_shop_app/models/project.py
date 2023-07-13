# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import api, fields, models, _


class ProjectProject(models.Model):
    _inherit = 'project.project'

    services_ids = fields.One2many('project.service', 'project_id')
    qr_code = fields.Binary(string='QR code', copy=False)

    @api.onchange('services_ids')
    def onchange_services_ids(self):
        for line in self.services_ids:
            branch_ids = line.product_id.signal_ids.mapped('branch_id').ids
            current_id = self._origin.id
            if current_id in branch_ids:
                signal = self.env['service.signal.line'].search(
                    [('branch_id', '=', current_id), ('service_id', '=', line.product_id.id)])
                for sig in signal:
                    line.signal = sig.signal
                    line.duration = sig.duration


class ProjectService(models.Model):
    _name = 'project.service'

    project_id = fields.Many2one('project.project', string='Project')
    product_id = fields.Many2one('product.product', string='Service', domain=[('is_service', '=', True)])
    signal = fields.Char(string='Signal')
    duration = fields.Float(string='Duration')
