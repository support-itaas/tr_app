/**
 * Created by brucenguyen on 4/27/17.
 */
"use strict";
odoo.define('pos_retail.screen_voucher', function (require) {

    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var _t = core._t;
    var gui = require('point_of_sale.gui');
    var qweb = core.qweb;
    var PopupWidget = require('point_of_sale.popups');
    var rpc = require('pos.rpc');
    var models = require('point_of_sale.models');

    models.load_models([
        {
            model: 'pos.voucher',
            fields: ['code', 'value', 'apply_type', 'method', 'use_date', 'number'],
            domain: [['state', '=', 'active']],
            context: {'pos': true},
            loaded: function (self, vouchers) {
                self.vouchers = vouchers;
                self.voucher_by_id = {};
                for (var x = 0; x < vouchers.length; x++) {
                    self.voucher_by_id[vouchers[x].id] = vouchers[x];
                }
            }
        }
    ]);

    var _super_PosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_model: function (_name) {
            var _index = this.models.map(function (e) {
                return e.model;
            }).indexOf(_name);
            if (_index > -1) {
                return this.models[_index];
            }
            return false;
        },
        initialize: function (session, attributes) {
            var wait_journal = this.get_model('account.journal');
            wait_journal.fields.push('pos_method_type');
            return _super_PosModel.initialize.apply(this, arguments);
        }
    });

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function () {
            var json = _super_Order.export_as_JSON.apply(this, arguments);
            if (this.voucher_id) {
                json.voucher_id = parseInt(this.voucher_id);
            }
            return json;
        }
    });

    var _super_Paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        init_from_JSON: function (json) {
            var res = _super_Paymentline.init_from_JSON.apply(this, arguments);
            if (json.voucher_id) {
                this.voucher_id = json.voucher_id
            }
            if (json.voucher_code) {
                this.voucher_code = json.voucher_code
            }
            return res
        },
        export_as_JSON: function () {
            var json = _super_Paymentline.export_as_JSON.apply(this, arguments);
            if (this.voucher_id) {
                json['voucher_id'] = this.voucher_id;
            }
            if (this.voucher_code) {
                json['voucher_code'] = this.voucher_code;
            }
            return json
        },
        export_for_printing: function () {
            var datas = _super_Paymentline.export_for_printing.apply(this, arguments);
            if (this.voucher_code) {
                datas['voucher_code'] = this.voucher_code
            }
            return datas
        }
    });

    screens.OrderWidget.include({
        active_button_print_voucher: function (buttons, selected_order) {
            if (buttons.button_print_voucher) {
                if (this.pos.config.iface_print_via_proxy) {
                    buttons.button_print_voucher.highlight(true);
                } else {
                    buttons.button_print_voucher.highlight(false);
                }
            }
        },
        update_summary: function () {
            this._super();
            var selected_order = this.pos.get_order();
            var buttons = this.getParent().action_buttons;
            if (selected_order && buttons) {
                this.active_button_print_voucher(buttons);
            }
        }
    });

    screens.PaymentScreenWidget.include({
        renderElement: function () {
            var self = this;
            this._super();
            this.$('.input_voucher').click(function () { // input manual voucher
                self.hide();
                return self.pos.gui.show_popup('alert_input', {
                    title: _t('Voucher'),
                    body: _t('Please input code or number of voucher.'),
//                    console.log('INPUT VOCHER')
                    confirm: function (code) {
                        self.show();
                        self.renderElement();
                        if (!code) {
                            return false;
                        } else {
                            return rpc.query({
                                model: 'pos.voucher',
                                method: 'get_voucher_by_code',
                                args: [code],
                            }).then(function (voucher) {
                                if (voucher == -1) {
                                    return self.gui.show_popup('confirm', {
                                        title: 'Warning',
                                        body: 'Voucher code used before or code doest not exist'
                                    });
                                } else {
                                    var current_order = self.pos.get('selectedOrder');
                                    current_order.voucher_id = voucher.id;
                                    var voucher_register = _.find(self.pos.cashregisters, function (cashregister) {
                                        return cashregister.journal['pos_method_type'] == 'voucher';
                                    });
                                    if (voucher_register) {
                                        if (voucher['customer_id'] && voucher['customer_id'][0]) {
                                            var client = self.pos.db.get_partner_by_id(voucher['customer_id'][0]);
                                            if (client) {
                                                current_order.set_client(client)
                                            }
                                        }
                                        var amount = 0;
                                        if (voucher['apply_type'] == 'fixed_amount') {
                                            amount = voucher.value;
                                        } else {
                                            amount = current_order.get_total_with_tax() / 100 * voucher.value;
                                        }
                                        if (amount <= 0) {
                                            return self.pos.gui.show_popup('confirm', {
                                                title: 'Warning',
                                                body: 'Voucher limited value',
                                            });
                                        }
                                        // remove old paymentline have journal is voucher
                                        var paymentlines = current_order.paymentlines;
                                        for (var i = 0; i < paymentlines.models.length; i++) {
                                            var payment_line = paymentlines.models[i];
                                            if (payment_line.cashregister.journal['pos_method_type'] == 'voucher') {
                                                payment_line.destroy();
                                            }
                                        }
                                        // add new payment with this voucher just scanned
                                        var voucher_paymentline = new models.Paymentline({}, {
                                            order: current_order,
                                            cashregister: voucher_register,
                                            pos: self.pos
                                        });
                                        var due = current_order.get_due();
                                        if (amount >= due) {
                                            voucher_paymentline.set_amount(due);
                                        } else {
                                            voucher_paymentline.set_amount(amount);
                                        }
                                        voucher_paymentline['voucher_id'] = voucher['id'];
                                        voucher_paymentline['voucher_code'] = voucher['code'];
                                        current_order.paymentlines.add(voucher_paymentline);
                                        current_order.trigger('change', current_order);
                                        self.render_paymentlines();
                                        self.$('.paymentline.selected .edit').text(self.format_currency_no_symbol(amount));
                                        return self.pos.gui.show_popup('confirm', {
                                            title: 'Finished',
                                            body: 'Add voucher with amount ' + amount,
                                        });
                                    } else {
                                        return self.pos.gui.show_popup('confirm', {
                                            title: 'Warning',
                                            body: 'POS config not add payment method Voucher. Please add method voucher, close and reopen session',
                                        });
                                    }

                                }
                            }).fail(function (type, error) {
                                return self.pos.query_backend_fail(type, error);
                            });
                        }
                    },
                    cancel: function () {
                        self.show();
                        self.renderElement();
                    }
                });
            });
        },
        render_paymentlines: function () {
            this._super();
            // Show || Hide Voucher method
            // find voucher journal inside this pos
            // and hide this voucher element, because if display may be made seller confuse
            var voucher_journal = _.find(this.pos.cashregisters, function (cashregister) {
                return cashregister.journal['pos_method_type'] == 'voucher';
            });
            if (voucher_journal) {
                var voucher_journal_id = voucher_journal.journal.id;
                var voucher_journal_content = $("[data-id='" + voucher_journal_id + "']");
                voucher_journal_content.addClass('oe_hidden');
            }
        },
        // Active device scan barcode voucher
        show: function () {
            var self = this;
            this._super();
            this.pos.barcode_reader.set_action_callback({
                'voucher': _.bind(self.barcode_voucher_action, self),
            });
        },
        // scan voucher viva device
        barcode_voucher_action: function (datas) {
            var self = this;
            this.datas_code = datas;
            rpc.query({
                model: 'pos.voucher',
                method: 'get_voucher_by_code',
                args: [datas['code']],
            }).then(function (voucher) {
                if (voucher == -1) {
                    return self.pos.gui.show_popup('confirm', {
                        title: 'Warning',
                        body: 'Voucher expired date or used before',
                    });
                } else {
                    var current_order = self.pos.get('selectedOrder');
                    current_order.voucher_id = voucher.id;
                    var voucher_register = _.find(self.pos.cashregisters, function (cashregister) {
                        return cashregister.journal['pos_method_type'] == 'voucher';
                    });
                    if (voucher_register) {
                        if (voucher['customer_id'] && voucher['customer_id'][0]) {
                            var client = self.pos.db.get_partner_by_id(voucher['customer_id'][0]);
                            if (client) {
                                current_order.set_client(client)
                            }
                        }
                        var amount = 0;
                        if (voucher['apply_type'] == 'fixed_amount') {
                            amount = voucher.value;
                        } else {
                            amount = current_order.get_total_with_tax() / 100 * voucher.value;
                        }
                        if (amount <= 0) {
                            return self.pos.gui.show_popup('confirm', {
                                title: 'Warning',
                                body: 'Voucher limited value',
                            });
                        }
                        // remove old paymentline have journal is voucher
                        var paymentlines = current_order.paymentlines;
                        for (var i = 0; i < paymentlines.models.length; i++) {
                            var payment_line = paymentlines.models[i];
                            if (payment_line.cashregister.journal['pos_method_type'] == 'voucher') {
                                payment_line.destroy();
                            }
                        }
                        // add new payment with this voucher just scanned
                        var voucher_paymentline = new models.Paymentline({}, {
                            order: current_order,
                            cashregister: voucher_register,
                            pos: self.pos
                        });
                        voucher_paymentline['voucher_id'] = voucher['id'];
                        voucher_paymentline['voucher_code'] = voucher['code'];
                        var due = current_order.get_due();
                        if (amount >= due) {
                            voucher_paymentline.set_amount(due);
                        } else {
                            voucher_paymentline.set_amount(amount);
                        }
                        voucher_paymentline['voucher_id'] = voucher['id'];
                        current_order.paymentlines.add(voucher_paymentline);
                        current_order.trigger('change', current_order);
                        self.render_paymentlines();
                        self.$('.paymentline.selected .edit').text(self.format_currency_no_symbol(amount));
                    } else {
                        return self.pos.gui.show_popup('confirm', {
                            title: 'Warning',
                            body: 'POS config not add payment method Voucher. Please add method voucher, close and reopen session',
                        });
                    }

                }
            }).fail(function (type, error) {
                return self.pos.query_backend_fail(type, error);
            });
            return true;
        }
    });

    var vouchers_screen = screens.ScreenWidget.extend({
        template: 'vouchers_screen',

        show: function () {
            this._super();
            this.vouchers = this.pos.vouchers_created;
            this.render_vouchers();
            this.handle_auto_print();
        },
        handle_auto_print: function () {
            if (this.should_auto_print()) {
                this.print();
                if (this.should_close_immediately()) {
                    this.click_back();
                }
            } else {
                this.lock_screen(false);
            }
        },
        should_auto_print: function () {
            return this.pos.config.iface_print_auto;
        },
        should_close_immediately: function () {
            return this.pos.config.iface_print_via_proxy;
        },
        lock_screen: function (locked) {
            this.$('.back').addClass('highlight');
            window.print();
        },
        get_voucher_env: function (voucher) {
            var order = this.pos.get_order();
            var datas = order.export_for_printing();
            return {
                widget: this,
                pos: this.pos,
                order: order,
                datas: datas,
                voucher: voucher
            };
        },
        print_web: function () {
            window.print();
        },
        print_xml: function () {
            if (this.vouchers) {
                for (var i = 0; i < this.vouchers.length; i++) {
                    var voucher_xml = qweb.render('voucher_ticket_xml', this.get_voucher_env(this.vouchers[i]));
                    this.pos.proxy.print_receipt(voucher_xml);
                }
            }
        },
        print: function () {
            var self = this;
            if (!this.pos.config.iface_print_via_proxy) {
                this.lock_screen(true);
                setTimeout(function () {
                    self.lock_screen(false);
                }, 1000);

                this.print_web();
            } else {
                this.print_xml();
                this.lock_screen(false);
            }
        },
        click_back: function () {
            this.pos.gui.show_screen('products');
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.$('.back').click(function () {
                self.click_back();
            });
            this.$('.button.print').click(function () {
                self.print();
            });
        },
        render_change: function () {
            this.$('.change-value').html(this.format_currency(this.pos.get_order().get_change()));
        },
        render_vouchers: function () {
            var $voucher_content = this.$('.pos-receipt-container');
            var url_location = window.location.origin + '/report/barcode/EAN13/';
            $voucher_content.empty();
            if (this.vouchers) {
                for (var i = 0; i < this.vouchers.length; i++) {
                    this.vouchers[i]['url_barcode'] = url_location + this.vouchers[i]['code'];
                    $voucher_content.append(
                        qweb.render('voucher_ticket_html', this.get_voucher_env(this.vouchers[i]))
                    );
                }
            }
        }
    });
    gui.define_screen({name: 'vouchers_screen', widget: vouchers_screen});

    // print vouchers
    var popup_print_vouchers = PopupWidget.extend({
        template: 'popup_print_vouchers',
        show: function (options) {
            var self = this;
            this._super(options);
            this.$('.print-voucher').click(function () {
                var validate;
                var number = parseFloat(self.$('.number').val());
                var period_days = parseFloat(self.$('.period_days').val());
                var apply_type = self.$('.apply_type').val();
                var voucher_amount = parseFloat(self.$('.voucher_amount').val());
                var quantity_create = parseInt(self.$('.quantity_create').val());
                var method = self.$('.method').val();
                var customer = self.pos.get_order().get_client();
                if (method == "special_customer" && !customer) {
                    this.pos.gui.show_popup('confirm', {
                        title: 'Warning',
                        body: 'Because apply to special customer, required select customer the first'
                    });
                    return self.pos.gui.show_screen('clientlist')
                }
                if (isNaN(number)) {
                    self.wrong_input('.number');
                    validate = false;
                } else {
                    self.passed_input('.number');
                }
                if (typeof period_days != 'number' || isNaN(period_days) || period_days <= 0) {
                    self.wrong_input('.period_days');
                    validate = false;
                } else {
                    self.passed_input('.period_days');
                }
                if (typeof voucher_amount != 'number' || isNaN(voucher_amount) || voucher_amount <= 0) {
                    self.wrong_input('.voucher_amount');
                    validate = false;
                } else {
                    self.passed_input('.voucher_amount');
                }
                if (typeof quantity_create != 'number' || isNaN(quantity_create) || quantity_create <= 0) {
                    self.wrong_input('.quantity_create');
                    validate = false;
                } else {
                    self.passed_input('.quantity_create');
                }
                if (validate == false) {
                    return;
                }
                var voucher_data = {
                    apply_type: apply_type,
                    value: voucher_amount,
                    method: method,
                    period_days: period_days,
                    total_available: quantity_create,
                    number: number
                };
                if (customer) {
                    voucher_data['customer_id'] = customer['id'];
                }
                self.gui.close_popup();
                return rpc.query({
                    model: 'pos.voucher',
                    method: 'create_voucher',
                    args: [voucher_data]
                }).then(function (vouchers_created) {
                    self.pos.vouchers_created = vouchers_created;
                    self.pos.gui.show_screen('vouchers_screen', {});
                }).fail(function (type, error) {
                    return self.pos.query_backend_fail(type, error);
                });
            });
            this.$('.cancel').click(function () {
                self.click_cancel();
            });
        }
    });
    gui.define_popup({
        name: 'popup_print_vouchers',
        widget: popup_print_vouchers
    });

    var button_print_voucher = screens.ActionButtonWidget.extend({
        template: 'button_print_voucher',
        button_click: function () {
            this.gui.show_popup('popup_print_vouchers', {});

        }
    });
    screens.define_action_button({
        'name': 'button_print_voucher',
        'widget': button_print_voucher,
        'condition': function () {
            return this.pos.config.print_voucher;
        }
    });
});