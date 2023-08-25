/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.change_detector', function (require) {
    "use strict";
    var chrome = require('point_of_sale.chrome');
    var bus = require('bus.bus').bus;
    var rpc = require('web.rpc');
    var indexedDB = require('pos_speed_up.indexedDB');
    var models = require('point_of_sale.models');
    var ProductListWidget = require('point_of_sale.screens').ProductListWidget;

    if(!indexedDB){
        return;
    }

    var _super_pos = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.count_sync = 0;
            _super_pos.initialize.call(this, session, attributes);
        },
        synch_without_reload: function (change_detector) {
            change_detector.set_status('connecting');

            var self = this;

            $.when(indexedDB.get('products'), indexedDB.get('customers')).then(function (products, customers) {
                // order_by product
                indexedDB.order_by_in_place(products, ['sequence', 'default_code', 'name'], 'esc');

                // add product
                self.db.product_by_category_id = {};
                self.db.category_search_string = {};
                self.p_super_loaded(self, products);

                // add customer
                self.c_super_loaded(self, customers);

                // re-render products
                var products_screen = self.gui.screen_instances['products'];
                products_screen.product_list_widget = new ProductListWidget(products_screen, {
                    click_product_action: function (product) {
                        products_screen.click_product(product);
                    },
                    product_list: self.db.get_product_by_category(products_screen.product_categories_widget.category.id)
                });
                products_screen.product_list_widget.replace($('.product-list-container'));
                products_screen.product_categories_widget.product_list_widget = products_screen.product_list_widget;
                // -end-

                setTimeout(function () {
                    change_detector.set_status('connected');
                }, 500);

                // reset count
                self.count_sync = 0;

            }).fail(function(){
                change_detector.set_status('disconnected', self.count_sync);
            });
        }
    });

    var ChangeDetectorWidget = chrome.StatusWidget.extend({
        template: 'ChangeDetectorWidget',

        set_status: function (status, msg) {
            for (var i = 0; i < this.status.length; i++) {
                this.$('.jane_' + this.status[i]).addClass('oe_hidden');
            }
            this.$('.jane_' + status).removeClass('oe_hidden');

            if (msg) {
                this.$('.jane_msg').removeClass('oe_hidden').text(msg);
            } else {
                this.$('.jane_msg').addClass('oe_hidden').html('');
            }
        },
        start: function () {
            var self = this;

            bus.on('notification', this, function (notifications) {
                var data = notifications.filter(function (item) {
                    return item[0][1] === 'change_detector';
                }).map(function (item) {
                    return item[1];
                });

                var p = data.filter(function(item){
                    return item.p;
                });
                var c = data.filter(function(item){
                    return item.c;
                });
                self.on_change(p, c);
            });

            this.$el.click(function () {
                self.pos.synch_without_reload(self);
            });
        },
        on_change: function (p, c) {
            if (p.length > 0) {
                this.p_sync_not_reload(p.p);
            }

            if (c.length > 0) {
                this.c_sync_not_reload(c.c);
            }
        },
        p_sync_not_reload: function (server_version) {
            var self = this;

            var model = self.pos.get_model('product.product');

            var client_version = localStorage.getItem('product_index_version');
            if (!/^\d+$/.test(client_version)) {
                client_version = 0;
            }

            if (client_version === server_version) {
                return;
            }

            rpc.query({
                model: 'product.index',
                method: 'sync_not_reload',
                args: [client_version, model.fields]
            }).then(function (res) {
                localStorage.setItem('product_index_version', res['latest_version']);

                // increase count
                self.pos.count_sync += res['create'].length + res['delete'].length;

                if (self.pos.count_sync > 0) {
                    self.set_status('disconnected', self.pos.count_sync);
                }

                indexedDB.get_object_store('products').then(function (store) {
                    _.each(res['create'], function (record) {
                        store.put(record).onerror = function (e) {
                            console.log(e);
                            localStorage.setItem('product_index_version', client_version);
                        }
                    });
                    _.each(res['delete'], function (id) {
                        store.delete(id).onerror = function (e) {
                            console.log(e);
                            localStorage.setItem('product_index_version', client_version);
                        };
                    });
                }).fail(function (error){
                    console.log(error);
                    localStorage.setItem('product_index_version', client_version);
                });
            });
        },
        c_sync_not_reload: function (server_version) {
            var self = this;

            var model = self.pos.get_model('res.partner');

            var client_version = localStorage.getItem('customer_index_version');
            if (!/^\d+$/.test(client_version)) {
                client_version = 0;
            }

            if (client_version === server_version) {
                return;
            }

            rpc.query({
                model: 'customer.index',
                method: 'sync_not_reload',
                args: [client_version, model.fields]
            }).then(function (res) {
                localStorage.setItem('customer_index_version', res['latest_version']);

                self.pos.count_sync += res['create'].length + res['delete'].length;

                if (self.pos.count_sync > 0) {
                    self.set_status('disconnected', self.pos.count_sync);
                }

                indexedDB.get_object_store('customers').then(function (store) {
                    _.each(res['create'], function (record) {
                        store.put(record).onerror = function (e) {
                            console.log(e);
                            localStorage.setItem('customer_index_version', client_version);
                        }
                    });
                    _.each(res['delete'], function (id) {
                        store.delete(id).onerror = function (e) {
                            console.log(e);
                            localStorage.setItem('customer_index_version', client_version);
                        };
                    });
                }).fail(function (error) {
                    console.log(error);
                    localStorage.setItem('customer_index_version', client_version);
                });

                // clear dom cache for re-render customers
                var partner_screen = self.gui.screen_instances['clientlist'];
                var partner_cache = partner_screen.partner_cache;
                res['create'].map(function (partner) {
                    return partner.id;
                }).concat(res['delete']).forEach(function (partner_id) {
                    partner_cache.clear_node(partner_id);
                });
            });
        }
    });


    chrome.SynchNotificationWidget.include({
         renderElement: function(){
            new ChangeDetectorWidget(this, {}).appendTo('.pos-rightheader');
            this._super();
        }
    });

});