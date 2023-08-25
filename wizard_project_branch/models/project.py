# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
from odoo import models, fields, api


class Project(models.Model):
    _inherit = 'project.project'

    image_ids = fields.One2many('branch.images', 'project_id', string="Branch Image")
    operating_branch_id = fields.Many2one('operating.unit', 'Operating Branch')
    latitude = fields.Float(string="Latitude", related='partner_id.partner_latitude', )
    longitude = fields.Float(string="Longitude", related='partner_id.partner_longitude', )
    address_string = fields.Char(compute='compute_address_string')
    is_branch = fields.Boolean(string='Is A Branch', default=False)


    @api.multi
    def compute_address_string(self):
        for project in self:
            address_string = []
            if project.partner_id:
                if project.partner_id.street:
                    address_string.append(project.partner_id.street)
                if project.partner_id.street2:
                    address_string.append(project.partner_id.street2)
                if project.partner_id.city:
                    address_string.append(project.partner_id.city)
                if project.partner_id.state_id and project.partner_id.state_id.name:
                    address_string.append(project.partner_id.state_id.name)
                if project.partner_id.zip:
                    address_string.append(project.partner_id.zip)
                if project.partner_id.phone:
                    address_string.append(' Tel: ' + project.partner_id.phone)
            address = ' ,'.join(address_string)
            project.address_string = address
