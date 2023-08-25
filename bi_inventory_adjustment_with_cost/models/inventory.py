# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, pycompat
from odoo.tools import float_utils

class ResCompany(models.Model):
	_inherit='res.company'

	
	inv_cost = fields.Boolean(default=False)


class Inventory(models.Model):

	_inherit = 'stock.inventory'

	inv_cost = fields.Boolean(default=False,related="company_id.inv_cost")


class InventoryLine(models.Model):

	_inherit = 'stock.inventory.line'

	unit_price = fields.Float(string="Cost Price",readonly=False)

	@api.model
	def default_get(self,fields):
		res = super(InventoryLine, self).default_get(fields)

		if 'unit_price' in fields and res.get('product_id'):
			res['unit_price'] = self.env['product.product'].browse(res['product_id']).standard_price
		return res

	def _get_move_values(self, qty, location_id, location_dest_id, out):
		self.ensure_one()
		res = super(InventoryLine,self)._get_move_values(qty, location_id, location_dest_id, out)
		res.update({
			'price_unit':self.unit_price
			})
		return res
		
	@api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
	def _onchange_quantity_context(self):
		if self.product_id and self.location_id and self.product_id.uom_id.category_id == self.product_uom_id.category_id:  # TDE FIXME: last part added because crash
			self._compute_theoretical_qty()
			self.product_qty = self.theoretical_qty
			self.unit_price = self.product_id.standard_price

	@api.onchange('price_unit')
	def _onchange_price_unit(self):
		self.move_ids.price_unit = self.line_ids.unit_price

	def _generate_moves(self):
		moves = self.env['stock.move']
		for line in self:
			if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
				continue
			diff = line.theoretical_qty - line.product_qty
			if diff < 0:  # found more than expected
				vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, line.location_id.id, False)
			else:
				vals = line._get_move_values(abs(diff), line.location_id.id, line.product_id.property_stock_inventory.id, True)
			moves |= self.env['stock.move'].create(vals)
		return moves

class InventoryIn(models.Model):

	_inherit = 'stock.inventory'

	def _get_inventory_lines_values(self):
		# TDE CLEANME: is sql really necessary ? I don't think so
		locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
		domain = ' location_id in %s AND quantity != 0 AND active = TRUE'
		args = (tuple(locations.ids),)

		vals = []
		Product = self.env['product.product']
		# Empty recordset of products available in stock_quants
		quant_products = self.env['product.product']
		# Empty recordset of products to filter
		products_to_filter = self.env['product.product']

		# case 0: Filter on company
		if self.company_id:
			domain += ' AND company_id = %s'
			args += (self.company_id.id,)

		#case 1: Filter on One owner only or One product for a specific owner
		if self.partner_id:
			domain += ' AND owner_id = %s'
			args += (self.partner_id.id,)
		#case 2: Filter on One Lot/Serial Number
		if self.lot_id:
			domain += ' AND lot_id = %s'
			args += (self.lot_id.id,)
		#case 3: Filter on One product
		if self.product_id:
			domain += ' AND product_id = %s'
			args += (self.product_id.id,)
			products_to_filter |= self.product_id
		#case 4: Filter on A Pack
		if self.package_id:
			domain += ' AND package_id = %s'
			args += (self.package_id.id,)
		#case 5: Filter on One product category + Exahausted Products
		if self.category_id:
			categ_products = Product.search([('categ_id', 'child_of', self.category_id.id)])
			domain += ' AND product_id = ANY (%s)'
			args += (categ_products.ids,)
			products_to_filter |= categ_products

		self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
			FROM stock_quant
			LEFT JOIN product_product
			ON product_product.id = stock_quant.product_id
			WHERE %s
			GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)

		for product_data in self.env.cr.dictfetchall():
			# replace the None the dictionary by False, because falsy values are tested later on
			for void_field in [item[0] for item in product_data.items() if item[1] is None]:
				product_data[void_field] = False
			product_data['theoretical_qty'] = product_data['product_qty']
			if product_data['product_id']:
				product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
				product_data['unit_price'] = Product.browse(product_data['product_id']).standard_price
				
				quant_products |= Product.browse(product_data['product_id'])
			vals.append(product_data)
		if self.exhausted:
			exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
			vals.extend(exhausted_vals)
		return vals	


class StockMoveLine(models.Model):

	_inherit = 'stock.move'

	unit_price = fields.Float(related='price_unit')


	def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
		"""
		Generate the account.move.line values to post to track the stock valuation difference due to the
		processing of the given quant.
		"""
		self.ensure_one()

		if self._context.get('force_valuation_amount'):
			valuation_amount = self._context.get('force_valuation_amount')
		else:
			valuation_amount = cost

		if self._context.get('forced_ref'):
			ref = self._context['forced_ref']
		else:
			ref = self.picking_id.name
		# the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
		# the company currency... so we need to use round() before creating the accounting entries.
		debit_value = self.company_id.currency_id.round(valuation_amount)
		if self.product_id.cost_method == 'standard' and self.price_unit > 0.00:
			value = self.price_unit * self.product_uom_qty
			debit_value = self.company_id.currency_id.round(value)
		elif self.product_id.cost_method == 'fifo' and self.price_unit > 0.00:
			value = self.price_unit * self.product_uom_qty
			debit_value = self.company_id.currency_id.round(value)
		elif self.product_id.cost_method == 'average' and self.price_unit > 0.00:
			value = self.price_unit * self.product_uom_qty
			debit_value = self.company_id.currency_id.round(value)

		# check that all data is correct
		if self.company_id.currency_id.is_zero(debit_value) and not self.env['ir.config_parameter'].sudo().get_param('stock_account.allow_zero_cost'):
			raise UserError(_("The cost of %s is currently equal to 0. Change the cost or the configuration of your product to avoid an incorrect valuation.") % (self.product_id.display_name,))
		credit_value = debit_value
		partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
		debit_line_vals = {
			'name': self.name,
			'product_id': self.product_id.id,
			'quantity': qty,
			'product_uom_id': self.product_id.uom_id.id,
			'ref': ref,
			'partner_id': partner_id,
			'debit': debit_value if debit_value > 0 else 0,
			'credit': -debit_value if debit_value < 0 else 0,
			'account_id': debit_account_id,
		}
		credit_line_vals = {
			'name': self.name,
			'product_id': self.product_id.id,
			'quantity': qty,
			'product_uom_id': self.product_id.uom_id.id,
			'ref': ref,
			'partner_id': partner_id,
			'credit': credit_value if credit_value > 0 else 0,
			'debit': -credit_value if credit_value < 0 else 0,
			'account_id': credit_account_id,
		}
		res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
		if credit_value != debit_value:
			# for supplier returns of product in average costing method, in anglo saxon mode
			diff_amount = debit_value - credit_value
			price_diff_account = self.product_id.property_account_creditor_price_difference
			if not price_diff_account:
				price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
			if not price_diff_account:
				raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
			price_diff_line = {
				'name': self.name,
				'product_id': self.product_id.id,
				'quantity': qty,
				'product_uom_id': self.product_id.uom_id.id,
				'ref': ref,
				'partner_id': partner_id,
				'credit': diff_amount > 0 and diff_amount or 0,
				'debit': diff_amount < 0 and -diff_amount or 0,
				'account_id': price_diff_account.id,
			}
			res.append((0, 0, price_diff_line))
		return res


	def _run_valuation(self, quantity=None):
		self.ensure_one()
		value_to_return = 0
		if self._is_in():
			valued_move_lines = self.move_line_ids.filtered(lambda ml: not ml.location_id._should_be_valued() and ml.location_dest_id._should_be_valued() and not ml.owner_id)
			valued_quantity = 0
			for valued_move_line in valued_move_lines:
				valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, self.product_id.uom_id)
			# Note: we always compute the fifo `remaining_value` and `remaining_qty` fields no
			# matter which cost method is set, to ease the switching of cost method.
			vals = {}
			price_unit = self._get_price_unit()
			value = price_unit * (quantity or valued_quantity)
			value_to_return = value if quantity is None or not self.value else self.value
			if self.price_unit <= 0.00:
				self.write({
					'price_unit': price_unit,
					'value': value_to_return,
					'remaining_value': value if quantity is None else self.remaining_value + value,
				})
			else:
				self.write({
					'price_unit':self.price_unit,
					'value': value_to_return,
					'remaining_value': value if quantity is None else self.remaining_value + value,
				})
			vals['remaining_qty'] = valued_quantity if quantity is None else self.remaining_qty + quantity
			if self.product_id.cost_method == 'standard':
				value = self.product_id.standard_price * (quantity or valued_quantity)
				value_to_return = value if quantity is None or not self.value else self.value
				if self.price_unit <= 0.00:
					self.write({
						'price_unit': self.product_id.standard_price,
						'value': value_to_return,
					})
				else:
					self.write({
						'price_unit': self.price_unit,
						'value': value_to_return,
					})

		if self._is_out():
			valued_move_lines = self.move_line_ids.filtered(lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
			valued_quantity = 0
			for valued_move_line in valued_move_lines:
				valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, self.product_id.uom_id)
			self.env['stock.move'].with_context(price_unit=self.price_unit)._run_fifo(self, quantity=quantity)
			if self.product_id.cost_method in ['standard', 'average']:
				curr_rounding = self.company_id.currency_id.rounding
				if self.price_unit == 0.00:
					value = -float_round(self.product_id.standard_price * (valued_quantity if quantity is None else quantity), precision_rounding=curr_rounding)
					value_to_return = value if quantity is None else self.value + value

					self.write({
						'value': value_to_return,
						'price_unit': value / valued_quantity,
					})
				else:
					value = -float_round(self.price_unit * (valued_quantity if quantity is None else quantity), precision_rounding=curr_rounding)
					value_to_return = value if quantity is None else self.value + value

					self.write({
						'value': value_to_return,
						'price_unit': self.price_unit,
					})

		elif self._is_dropshipped() or self._is_dropshipped_returned():
			curr_rounding = self.company_id.currency_id.rounding
			if self.product_id.cost_method in ['fifo']:
				price_unit = self._get_price_unit()
				# see test_dropship_fifo_perpetual_anglosaxon_ordered
				self.product_id.standard_price = price_unit
			else:
				price_unit = self.product_id.standard_price
			value = float_round(self.product_qty * price_unit, precision_rounding=curr_rounding)
			value_to_return = value if self._is_dropshipped() else -value
			# In move have a positive value, out move have a negative value, let's arbitrary say
			# dropship are positive.
			if self.price_unit <= 0.00:
				self.write({
					'value': value_to_return,
					'price_unit': price_unit if self._is_dropshipped() else -price_unit,
				})
			else:
				self.write({
					'value': value_to_return,
					'price_unit':self.price_unit ,
				})
		return value_to_return

	@api.model
	def _run_fifo(self, move, quantity=None):
		""" Value `move` according to the FIFO rule, meaning we consume the
		oldest receipt first. Candidates receipts are marked consumed or free
		thanks to their `remaining_qty` and `remaining_value` fields.
		By definition, `move` should be an outgoing stock move.

		:param quantity: quantity to value instead of `move.product_qty`
		:returns: valued amount in absolute
		"""
		move.ensure_one()

		print ('_run_fifo--->Value')

		# Deal with possible move lines that do not impact the valuation.
		valued_move_lines = move.move_line_ids.filtered(lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
		valued_quantity = 0
		for valued_move_line in valued_move_lines:
			valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)

		# Find back incoming stock moves (called candidates here) to value this move.
		qty_to_take_on_candidates = quantity or valued_quantity
		candidates = move.product_id._get_fifo_candidates_in_move()
		print('candidates', candidates)
		new_standard_price = 0
		tmp_value = 0  # to accumulate the value taken on the candidates
		for candidate in candidates:
			print('candidate-', candidate)
			new_standard_price = candidate.price_unit
			if candidate.remaining_qty <= qty_to_take_on_candidates:
				qty_taken_on_candidate = candidate.remaining_qty
			else:
				qty_taken_on_candidate = qty_to_take_on_candidates

			# As applying a landed cost do not update the unit price, naivelly doing
			# something like qty_taken_on_candidate * candidate.price_unit won't make
			# the additional value brought by the landed cost go away.
			print('candidate.remaining_value', candidate.remaining_value)
			print('candidate.remaining_qty', candidate.remaining_qty)
			candidate_price_unit = candidate.remaining_value / candidate.remaining_qty
			print('candidate_price_unit', candidate_price_unit)
			value_taken_on_candidate = qty_taken_on_candidate * candidate_price_unit
			candidate_vals = {
				'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
				'remaining_value': candidate.remaining_value - value_taken_on_candidate,
			}
			candidate.write(candidate_vals)

			qty_to_take_on_candidates -= qty_taken_on_candidate
			tmp_value += value_taken_on_candidate
			if qty_to_take_on_candidates == 0:
				break

		# Update the standard price with the price of the last used candidate, if any.
		# if new_standard_price and move.product_id.cost_method == 'fifo':
		# 	move.product_id.sudo().with_context(force_company=move.company_id.id) \
		# 		.standard_price = new_standard_price

		# If there's still quantity to value but we're out of candidates, we fall in the
		# negative stock use case. We chose to value the out move at the price of the
		# last out and a correction entry will be made once `_fifo_vacuum` is called.
		if qty_to_take_on_candidates == 0:
			move.write({
				'value': -tmp_value if not quantity else move.value or -tmp_value,  # outgoing move are valued negatively
				'price_unit': -tmp_value / (move.product_qty or quantity),
			})
		elif qty_to_take_on_candidates > 0:
			print ('qty_to_take_on_candidates > 0')
			if self._context.get('price_unit'):
				last_fifo_price = self._context.get('price_unit')

			# elif candidate_price_unit > 0:
			# 	last_fifo_price = candidate_price_unit
			else:
				if new_standard_price:
					last_fifo_price = new_standard_price
				else:
					standard_price = move.product_uom._compute_quantity(move.product_id.standard_price, move.product_id.uom_po_id, rounding_method='HALF-UP')

					last_fifo_price = standard_price

			print ('last_fifo_price',last_fifo_price)
			negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
			tmp_value += abs(negative_stock_value)
			print('tmp_value', tmp_value)
			vals = {
				'remaining_qty': move.remaining_qty + -qty_to_take_on_candidates,
				'remaining_value': move.remaining_value + negative_stock_value,
				'value': -tmp_value,
				'price_unit': -1 * last_fifo_price,
			}
			move.write(vals)
		return tmp_value


class ProductIn(models.Model):
	_inherit = 'product.product'

	@api.multi
	@api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value', 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation', 'product_tmpl_id.categ_id.property_valuation')
	def _compute_stock_value(self):
		StockMove = self.env['stock.move']
		to_date = self.env.context.get('to_date')

		real_time_product_ids = [product.id for product in self if product.product_tmpl_id.valuation == 'real_time']
		if real_time_product_ids:
			self.env['account.move.line'].check_access_rights('read')
			fifo_automated_values = {}
			query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
						 FROM account_move_line AS aml
						WHERE aml.product_id IN %%s AND aml.company_id=%%s %s
					 GROUP BY aml.product_id, aml.account_id"""
			params = (tuple(real_time_product_ids), self.env.user.company_id.id)
			if to_date:
				query = query % ('AND aml.date <= %s',)
				params = params + (to_date,)
			else:
				query = query % ('',)
			self.env.cr.execute(query, params=params)

			res = self.env.cr.fetchall()
			for row in res:
				fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

		product_values = {product.id: 0 for product in self}
		product_move_ids = {product.id: [] for product in self}

		if to_date:
			domain = [('product_id', 'in', self.ids), ('date', '<=', to_date)] + StockMove._get_all_base_domain()
			value_field_name = 'value'
		else:
			domain = [('product_id', 'in', self.ids)] + StockMove._get_all_base_domain()
			value_field_name = 'remaining_value'

		StockMove.check_access_rights('read')
		query = StockMove._where_calc(domain)
		StockMove._apply_ir_rules(query, 'read')
		from_clause, where_clause, params = query.get_sql()
		query_str = """
			SELECT stock_move.product_id, SUM(COALESCE(stock_move.{}, 0.0)), ARRAY_AGG(stock_move.id)
			FROM {}
			WHERE {}
			GROUP BY stock_move.product_id
		""".format(value_field_name, from_clause, where_clause)
		self.env.cr.execute(query_str, params)
		for product_id, value, move_ids in self.env.cr.fetchall():
			product_values[product_id] = value
			product_move_ids[product_id] = move_ids

		for product in self:
			price = product.stock_move_ids.search([('product_id','=',product.id)], order='id desc',limit=1).price_unit
			if product.cost_method in ['standard', 'average']:
				qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
				price_used = price or product.standard_price
				if to_date:
					price_used = product.get_history_price(
						self.env.user.company_id.id,
						date=to_date,
					)
				product.stock_value = price_used * qty_available
				product.qty_at_date = qty_available
			elif product.cost_method == 'fifo':
				qty_available = product.with_context(company_owned=True, owner_id=False).qty_available

				if to_date:
					if product.product_tmpl_id.valuation == 'manual_periodic':
						product.stock_value = price * qty_available or product_values[product.id]
						product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
						product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
					elif product.product_tmpl_id.valuation == 'real_time':
						valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
						value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (0, 0, [])
						product.stock_value = price * qty_available or value
						product.qty_at_date = quantity
						product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
				else:

					product.stock_value = price * qty_available or product_values[product.id]
					product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
					if product.product_tmpl_id.valuation == 'manual_periodic':
						product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
					elif product.product_tmpl_id.valuation == 'real_time':
						valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
						value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (0, 0, [])
						product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)

