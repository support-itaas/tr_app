# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd(<http://www.technaureus.com/>).

from psycopg2 import OperationalError, Error
from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                   in_date=None):
        params = self._context.get('params')
        if params and 'force_date' in params:
            self = self.sudo()
            quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                  strict=True)
            rounding = product_id.uom_id.rounding

            incoming_dates = [d for d in quants.mapped('in_date') if d]
            incoming_dates = [fields.Datetime.from_string(incoming_date) for incoming_date in incoming_dates]
            if in_date:
                incoming_dates += [in_date]
            # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
            # consider only the oldest one as being relevant.
            if incoming_dates:
                in_date = fields.Datetime.to_string(min(incoming_dates))
            else:
                in_date = fields.Datetime.now()

            for quant in quants:
                try:
                    with self._cr.savepoint():
                        self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                         log_exceptions=False)
                        quant.write({
                            'quantity': quant.quantity + quantity,
                            'in_date': params.get('force_date'),
                        })
                        # cleanup empty quants
                        if float_is_zero(quant.quantity, precision_rounding=rounding) and float_is_zero(
                                quant.reserved_quantity, precision_rounding=rounding):
                            quant.unlink()
                        break
                except OperationalError as e:
                    if e.pgcode == '55P03':  # could not obtain the lock
                        continue
                    else:
                        raise
            else:
                self.create({
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'quantity': quantity,
                    'lot_id': lot_id and lot_id.id,
                    'package_id': package_id and package_id.id,
                    'owner_id': owner_id and owner_id.id,
                    'in_date': params.get('force_date'),
                })
            return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id,
                                                owner_id=owner_id, strict=False,
                                                allow_negative=True), fields.Datetime.from_string(in_date)

        else:
            super(StockQuant, self)._update_available_quantity(product_id, location_id, quantity, lot_id=lot_id,
                                                               package_id=package_id, owner_id=owner_id,
                                                               in_date=in_date)
