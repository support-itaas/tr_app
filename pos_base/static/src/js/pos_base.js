odoo.define('pos_base', function (require) {
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var PopupWidget = require('point_of_sale.popups');

    PopupWidget.include({
        wrong_input: function (element) {
            this.$(element).css({
                'box-shadow': '0px 0px 0px 1px rgb(236, 5, 5) inset'
            });
        },
        passed_input: function (element) {
            this.$(element).css({
                'box-shadow': '0px 0px 0px 1px rgb(34, 206, 3) inset'
            })
        }
    });


    var alert_input = PopupWidget.extend({
        template: 'alert_input',
        show: function (options) {
            options = options || {};
            this._super(options);
            this.renderElement();
            this.$('input').focus();
        },
        click_confirm: function () {
            var value = this.$('input').val();
            this.gui.close_popup();
            if (this.options.confirm) {
                this.options.confirm.call(this, value);
            }
        }
    });
    gui.define_popup({name: 'alert_input', widget: alert_input});

    var alert_result = PopupWidget.extend({
        template: 'alert_result',
        show: function (options) {
            var self = this;
            var timer = 1000;
            if (options) {
                swal({
                    title: options.title,
                    text: options.body,
                    buttonsStyling: false,
                    confirmButtonClass: "btn btn-info",
                    timer: options.timer || timer
                }).catch(swal.noop)
            }
            this._super(options);
            $('.swal2-confirm').click(function () {
                self.click_confirm();
            });
            $('.swal2-cancel').click(function () {
                self.click_cancel();
            })
        }
    });
    gui.define_popup({name: 'alert_result', widget: alert_result});

    var alert_confirm = PopupWidget.extend({
        template: 'alert_confirm',
        show: function (options) {
            var self = this;
            if (options) {
                swal({
                    title: options.title,
                    text: options.body || '',
                    type: options.type || 'warning',
                    showCancelButton: true,
                    confirmButtonText: options.confirmButtonText || '',
                    cancelButtonText: options.cancelButtonText || '',
                    confirmButtonClass: "btn btn-success",
                    cancelButtonClass: "btn btn-danger",
                    buttonsStyling: false
                });
            }
            this._super(options);
            $('.swal2-confirm').click(function () {
                self.click_confirm();
            });
            $('.swal2-cancel').click(function () {
                self.click_cancel();
            })

        }
    });
    gui.define_popup({name: 'alert_confirm', widget: alert_confirm});
});
