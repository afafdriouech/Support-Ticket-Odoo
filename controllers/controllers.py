# -*- coding: utf-8 -*-
from odoo import http

import werkzeug
import json
import base64
from random import randint
import os
import datetime
import requests
import logging
_logger = logging.getLogger(__name__)

import odoo.http as http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.http_routing.models.ir_http import slug

class Portal(http.Controller):
    @http.route('/sav/acc/create', type="http", auth="public", website=True)
    def support_account_create(self, **kw):
        return http.request.render('ticket-module.account_create_page', {})

    @http.route('/sav/acc/create/process', type="http", auth="public", website=True)
    def support_account_create_process(self, **kw):

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

            # Create the new user
        new_user = request.env['res.users'].sudo().create(
            {'name': values['name'], 'login': values['login'], 'email': values['login'],
             'password': values['password']})

        #Remove all permissions
        new_user.groups_id = False

            #add them to the portal group so they can access the website
        group_portal = request.env['ir.model.data'].sudo().get_object('base', 'group_portal')
        group_portal.users = [(4, new_user.id)]

            # Automatically sign the new user in
        request.cr.commit()  # as authenticate will use its own cursor we need to commit the current transaction
        request.session.authenticate(request.env.cr.dbname, values['login'], values['password'])

            # Redirection to the support page
        return werkzeug.utils.redirect("")

    @http.route('/sav/ticket/submit', type="http", auth="public", website=True)
    def support_submit_ticket(self, **kw):
        """Let's public and registered user submit a support ticket"""
        person_name = ""
        if http.request.env.user.name != "Public user":
            person_name = http.request.env.user.name

        category_access = []
        for category_permission in http.request.env.user.groups_id:
            category_access.append(category_permission.id)

        ticket_categories = http.request.env['ticket.category'].sudo().search(
            ['|', ('access_group_ids', 'in', category_access), ('access_group_ids', '=', False)])

        setting_google_recaptcha_active = request.env['ir.default'].get('support.settings',
                                                                        'google_recaptcha_active')
        setting_google_captcha_client_key = request.env['ir.default'].get('support.settings',
                                                                          'google_captcha_client_key')
        setting_max_ticket_attachments = request.env['ir.default'].get('support.settings',
                                                                       'max_ticket_attachments')
        setting_max_ticket_attachment_filesize = request.env['ir.default'].get('support.settings',
                                                                               'max_ticket_attachment_filesize')

        return http.request.render('ticket-module.support_submit_ticket', {'categories': ticket_categories,
                                                                             'priorities': http.request.env['ticket.priority'].sudo().search(
                                                                                 []), 'person_name': person_name,
                                                                             'email': http.request.env.user.email,
                                                                             'setting_max_ticket_attachments': setting_max_ticket_attachments,
                                                                             'setting_max_ticket_attachment_filesize': setting_max_ticket_attachment_filesize,
                                                                             'setting_google_recaptcha_active': setting_google_recaptcha_active,
                                                                             'setting_google_captcha_client_key': setting_google_captcha_client_key,
                                                                        })

    @http.route('/sav/ticket/process', type="http", auth="public", website=True, csrf=True)
    def support_process_ticket(self, **kwargs):
        """Adds the support ticket to the database and sends out email"""
        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        if values['my_gold'] != "256":
            return "Bot Detected"

        setting_google_recaptcha_active = request.env['ir.default'].get('website.support.settings',
                                                                        'google_recaptcha_active')
        if setting_google_recaptcha_active:

            setting_google_captcha_secret_key = request.env['ir.default'].get('support.settings',
                                                                              'google_captcha_secret_key')

            # Redirect them back if they didn't answer the captcha
            if 'g-recaptcha-response' not in values:
                return werkzeug.utils.redirect("/sav/ticket/submit")

            payload = {'secret': setting_google_captcha_secret_key, 'response': str(values['g-recaptcha-response'])}
            response_json = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)

            if response_json.json()['success'] is not True:
                return werkzeug.utils.redirect("/sav/ticket/submit")

        my_attachment = ""
        file_name = ""

        create_dict = {'person_name': values['person_name'], 'category_id': values['category'],
                        'email': values['email'], 'description': values['description'],
                       'subject': values['subject'], 'attachment': my_attachment, 'attachment_filename': file_name}

        if http.request.env.user.name != "Public user":

            create_dict['channel'] = 'Website (User)'

            partner = http.request.env.user.partner_id
            create_dict['partner_id'] = partner.id

            if 'priority' in values:
                create_dict['priority_id'] = int(values['priority'])

            partner.message_post(body="Customer " + partner.name + " has sent in a new support ticket",
                                 subject="New Support Ticket")
        else:

            create_dict['channel'] = 'Website (Public)'
            if 'priority' in values:
                create_dict['priority_id'] = int(values['priority'])

            # Automatically assign the partner if email matches
            search_partner = request.env['res.partner'].sudo().search([('email', '=', values['email'])])
            if len(search_partner) > 0:
                create_dict['partner_id'] = search_partner[0].id

        new_ticket_id = request.env['support.ticket'].sudo().create(create_dict)
        if 'file' in values:

            for c_file in request.httprequest.files.getlist('file'):
                data = c_file.read()

                if c_file.filename:
                    request.env['ir.attachment'].sudo().create({
                        'name': c_file.filename,
                        'datas': base64.b64encode(data),
                        'datas_fname': c_file.filename,
                        'res_model': 'support.ticket',
                        'res_id': new_ticket_id.id
                    })

        return werkzeug.utils.redirect("/sav/ticket/thanks")

    @http.route('/sav/ticket/thanks', type="http", auth="public", website=True)
    def support_ticket_thanks(self, **kw):
        return http.request.render('ticket-module.thank_you', {})

    @http.route('/sav/ticket/view', type="http", auth="user", website=True)
    def support_ticket_view_list(self, **kw):
        """Displays the list of support tickets owned by the current user"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        # Determine which tickets the logged in user can see
        ticket_access = []

        # Can see own tickets
        ticket_access.append(http.request.env.user.partner_id.id)
        search_t = [('partner_id', 'in', ticket_access), ('partner_id', '!=', False)]

        if 'state' in values:
            search_t.append(('state_id', '=', int(values['state'])))

        support_tickets = request.env['support.ticket'].sudo().search(search_t)

        change_requests = request.env['support.ticket'].sudo().search(
            [('partner_id', 'in', ticket_access), ('partner_id', '!=', False)])

        ticket_states = request.env['ticket.state'].sudo().search([])

        return request.render('ticket-module.support_ticket_view_list',
                              {'support_tickets': support_tickets, 'ticket_count': len(support_tickets),
                               'change_requests': change_requests, 'request_count': len(change_requests),
                               'ticket_states': ticket_states})

    @http.route('/sav/ticket/view/<ticket>', type="http", auth="user", website=True)
    def support_ticket_view(self, ticket):
        """View a support ticket of the list of my tickets"""

        # Determine which tickets the logged in user can see
        ticket_access = []

        # Can see own tickets
        ticket_access.append(http.request.env.user.partner_id.id)

        setting_max_ticket_attachments = request.env['ir.default'].get('support.settings',
                                                                       'max_ticket_attachments')
        setting_max_ticket_attachment_filesize = request.env['ir.default'].get('support.settings',
                                                                               'max_ticket_attachment_filesize')

        # Only let the user this ticket is assigned to view it
        support_ticket = http.request.env['support.ticket'].sudo().search(
            [('partner_id', 'in', ticket_access), ('partner_id', '!=', False), ('id', '=', ticket)])[0]
        return http.request.render('ticket-module.support_ticket_view', {'support_ticket': support_ticket,
                                                                           'setting_max_ticket_attachments': setting_max_ticket_attachments,
                                                                           'setting_max_ticket_attachment_filesize': setting_max_ticket_attachment_filesize})

    @http.route('/sav/ticket/close',type="http", auth="user")
    def support_ticket_close(self, **kw):
        """Close the support ticket"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

        ticket = http.request.env['support.ticket'].sudo().search([('id','=',values['ticket_id'])])

        #check if this user owns this ticket
        if ticket.partner_id.id == http.request.env.user.partner_id.id or ticket.partner_id in http.request.env.user.partner_id.stp_ids:

            customer_closed_state = request.env['ir.model.data'].sudo().get_object('ticket-module', 'website_ticket_state_customer_closed')
            ticket.state_id = customer_closed_state

            ticket.close_time = datetime.datetime.now()
            ticket.close_date = datetime.date.today()

            diff_time = ticket.close_time - ticket.create_date
            ticket.time_to_close = diff_time.seconds

            #ticket.sla_active = False

            closed_state_mail_template = customer_closed_state.mail_template_id

            if closed_state_mail_template:
                closed_state_mail_template.send_mail(ticket.id, True)

        else:
            return "You do not have permission to close this commment"

        return werkzeug.utils.redirect("/sav/ticket/view/" + str(ticket.id))