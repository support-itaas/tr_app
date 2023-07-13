# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import api, fields, models, _


class InstallmentApi(models.Model):
    _name = 'installment.api'

    def get_config_datas(self):
        data = {}
        IrDefault = self.env['ir.default'].sudo()
        min_amount_install = IrDefault.get(
            'res.config.settings', "min_amount_install")
        if min_amount_install:
            data.update({"gbpay_install_min_amount": min_amount_install})
            return {"success": "true", "message": "Datas retrieved", "data": data}
        else:
            return {"success": "false", "message": "No Datas retrieved", "data": []}
