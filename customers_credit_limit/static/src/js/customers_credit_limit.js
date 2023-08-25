odoo.define('customers_credit_limit.js.credit_limit_state', function (require) {
  'use strict'
  var AbstractField = require('web.AbstractField')
  var core = require('web.core')
  var fieldRegistry = require('web.field_registry')

  var _t = core._t

  var SetLimitStatus = AbstractField.extend({
    init: function () {
      this._super.apply(this, arguments)
      this.classes = this.nodeOptions && this.nodeOptions.classes || {}
    },

    _renderReadonly: function () {
      this._super.apply(this, arguments)
      var LimitClass = this.classes[this.value] || 'default'
      if (this.value) {
        var title = this.value === 'within' && _t('Order Within Credit Limit') || this.value === 'out' && _t('Order Exceeds Credit Limit!') || this.value === 'none' && _t('Customer Has No Credit Limit!') || _t('Credit Limit Not Applicable')
        this.$el.attr({'title': title, 'style': 'display:inline'})
        this.$el.removeClass('text-success text-danger text-default text-info text-primary')
        this.$el.html($('<span> <i class="fa fa-lg fa-info-circle"/> ' + title + '</span>').addClass('label label-' + LimitClass))
      }
    }
  })
  fieldRegistry.add('limit_status', SetLimitStatus)
})
