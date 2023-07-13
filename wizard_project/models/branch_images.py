# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
from odoo import models, fields


class BranchImages(models.Model):
    _name = 'branch.images'

    image = fields.Binary('Image', attachment=True, required=1)
    project_id = fields.Many2one('project.project', string='Project', invisible=True, readonly=True)
