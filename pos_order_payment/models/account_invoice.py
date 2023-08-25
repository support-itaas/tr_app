# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    is_update_pack = fields.Boolean(string='Update Price',default=False)

    @api.multi
    def action_invoice_open(self):
        res = super(account_invoice, self).action_invoice_open()
        self.update_product_pack_to_aml()
        return res



    @api.multi
    def update_product_pack_to_aml(self):
        for invoice in self:
            if invoice.move_id:
                invoice.move_id.button_cancel()
                for line in invoice.invoice_line_ids:
                    pricelist = invoice.partner_id.property_product_pricelist
                    if not pricelist:
                        pricelist = self.env['product.pricelist'].search([],limit=1)
                    partner_id = invoice.partner_id
                    fiscal_position_id = False
                    aml_id = invoice.move_id.line_ids.filtered(lambda x: x.product_id == line.product_id)
                    if aml_id:
                        aml_id = aml_id[0]

                    total_amount = 0
                    pdt = line.product_id

                    if pdt.is_pack:
                        # count_product_pack = 0

                        count = 0
                        amt_apply = 0
                        for pd in pdt.product_pack_id:
                            total_amount = total_amount + (pd.product_quantity * self.env['pos.order']._get_pdt_price_(pd.product_id, partner_id, pricelist,
                                                                                       fiscal_position_id))


                        for p in pdt.product_pack_id:
                            # print ('PRODUCT',p.product_id.name)
                            count +=1
                            if line.invoice_line_tax_ids and line.invoice_line_tax_ids[0].price_include:
                                pack_price = line.invoice_line_tax_ids[0].compute_all(line.price_unit)['total_excluded']
                                # print ('INCLUDE -VAT')
                            else:
                                # print ('NO VAT or EXC')
                                pack_price = line.price_unit

                            coupon_price = self.env['pos.order']._get_pdt_price_(p.product_id, partner_id, pricelist,
                                                                     fiscal_position_id)
                            amt = (coupon_price / total_amount) * pack_price * p.product_quantity * line.quantity


                            if len(line.product_id.product_pack_id) == count:
                                amt = round((line.price_subtotal - amt_apply), 2)
                            else:
                                ######not last one, accumulate to amt_apply#####
                                amt_apply += round(amt,2)

                            if not aml_id:
                                # print ('NO AML')
                                aml_ids = invoice.move_id.line_ids.filtered(lambda x: x.name == line.name and x.product_id == p.product_id)
                                # print ('AML IDS',aml_ids)
                                if not aml_ids:
                                    aml_ids = invoice.move_id.line_ids.filtered(lambda x: x.name == line.name)
                                if not aml_ids:
                                    aml_ids = invoice.move_id.line_ids.filtered(lambda x: x.product_id == p.product_id)

                                if aml_ids:
                                    aml_id = aml_ids[0]

                            if aml_id and count == 1:
                                # print('YES AML and 1')
                                # print ('AMOUNT', amt)
                                if invoice.type == 'out_invoice':
                                    aml_id.with_context(check_move_validity=False).update({'credit': round(amt,2),'product_id': p.product_id.id,'quantity': p.product_quantity * line.quantity,'account_id': p.product_id.property_account_income_id.id})
                                else:
                                    aml_id.with_context(check_move_validity=False).update(
                                        {'debit': round(amt, 2),
                                         'product_id': p.product_id.id,
                                         'quantity': p.product_quantity * line.quantity,
                                         'account_id': p.product_id.property_account_income_id.id})

                            elif aml_id:
                                # print('YES AML and NOT 1')
                                aml_ids = invoice.move_id.line_ids.filtered(
                                    lambda x: x.name == line.name and x.product_id == p.product_id)
                                if aml_ids:
                                    #if the same product of product inside the pack
                                    aml_id = aml_ids[0]
                                    if invoice.type == 'out_invoice':
                                        aml_id.with_context(check_move_validity=False).update(
                                            {'credit': round(amt, 2), 'product_id': p.product_id.id,
                                             'quantity': p.product_quantity * line.quantity,
                                             'account_id': p.product_id.property_account_income_id.id})
                                    else:
                                        aml_id.with_context(check_move_validity=False).update(
                                            {'debit': round(amt, 2),
                                             'product_id': p.product_id.id,
                                             'quantity': p.product_quantity * line.quantity,
                                             'account_id': p.product_id.property_account_income_id.id})


                                #if no line is exactly the same product, then copy from the main product
                                else:
                                    # print ('AMT---',amt)
                                    if invoice.type == 'out_invoice':
                                        aml_new_id = aml_id.with_context(check_move_validity=False).copy()
                                        aml_new_id.with_context(check_move_validity=False).update({'credit': round(amt,2),'product_id': p.product_id.id,'quantity': p.product_quantity * line.quantity,'account_id': p.product_id.property_account_income_id.id})
                                    else:
                                        aml_new_id = aml_id.with_context(check_move_validity=False).copy()
                                        aml_new_id.with_context(check_move_validity=False).update(
                                            {'debit': round(amt, 2), 'product_id': p.product_id.id,
                                             'quantity': p.product_quantity * line.quantity,
                                             'account_id': p.product_id.property_account_income_id.id})


                for line in invoice.invoice_line_ids:
                    if line.product_id.is_pack:
                        aml_id = invoice.move_id.line_ids.filtered(lambda x: x.product_id == line.product_id)
                        aml_id.with_context(check_move_validity=False).sudo().unlink()

                invoice.move_id.post()
                invoice.is_update_pack = True



class account_invoice_pack(models.TransientModel):
    _name = 'account.invoice.pack'

    def update_product_pack(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['account.invoice'].browse(active_ids):
            record.update_product_pack_to_aml()

        return {'type': 'ir.actions.act_window_close'}
