# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).


from odoo import api, fields, models, tools, _


class Currency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency):
        exchange_params = self._context.get('exchange_params')
        if exchange_params and 'it_currency_rate' in exchange_params:
            from_exchange_rate = exchange_params.get('it_currency_rate')
            to_currency = to_currency.with_env(self.env)
            return to_currency.rate / from_exchange_rate
        else:
            return super(Currency , self)._get_conversion_rate(from_currency,to_currency)

