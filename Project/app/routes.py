# routes.py
from datetime import datetime
import io
from flask import  jsonify, render_template, request, url_for, flash, redirect, send_file
import openpyxl
from sqlalchemy import Transaction, func
from .forms import DeletePartnerForm, LoginForm,  PartnerForm, SmallStorageForm, TransactionForm
from .models import  Card, Partner,  SmallStorage, User, Partner
from .extensions import db
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash
import pytz
import pandas as pd
from io import BytesIO


def configure_routes(app):

    @app.route('/')
    def home():
        return render_template('home.html')

#log in system/////////////////////////////////////////////////////////////////////
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        
        form = LoginForm()
        if form.validate_on_submit():
            # Attempt to find the user by their username
            user = User.query.filter_by(username=form.username.data).first()
             # If a user is found and password matches
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('You have been logged in!', 'success')
                
                # If the user was trying to visit a page that requires login, redirect there
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash('Login Unsuccessful. Please check username or password', 'danger')
        
        return render_template('login.html', title='Login', form=form)
        

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('home'))
    
   #logic for small and partner/////////////////////////////////////////////////
    @app.route('/adjust_main_storage')
    def adjust_main_storage():
    
     return render_template('adjust_main_storage.html',)
                          

    @app.route('/partners', methods=['GET', 'POST'])
    def partners():
     form = PartnerForm()

     if form.validate_on_submit():
        name = form.name.data
        partner = Partner(name=name, balance=0)  # Initialize balance to 0
        db.session.add(partner)
        db.session.commit()
        flash('New partner created!', 'success')
        return redirect(url_for('partners'))

     if request.method == 'POST':
        if 'delete_partner' in request.form:
            partner_id = request.form.get('delete_partner')
            partner = Partner.query.get_or_404(partner_id)
            db.session.delete(partner)
            db.session.commit()
            flash('Partner deleted successfully!', 'success')
        elif 'transfer_amount' in request.form:
            partner_id = request.form.get('partner_id')
            quantity = int(request.form.get('quantity'))
            small_storage_id = request.form.get('small_storage_id')

            partner = Partner.query.get_or_404(partner_id)
            small_storage = SmallStorage.query.get_or_404(small_storage_id)

            # Update partner and small storage balances
            partner.balance -= quantity
            small_storage.quantity += quantity

            db.session.commit()
            flash('Transaction completed successfully!', 'success')
        elif 'return_quantity' in request.form:
            small_storage_id = request.form.get('small_storage_id')
            quantity_to_return = int(request.form.get('quantity_to_return'))

            small_storage = SmallStorage.query.get_or_404(small_storage_id)

            # Check if the return quantity is valid
            if quantity_to_return > 0 and quantity_to_return <= small_storage.quantity:
                # Update small storage quantity
                small_storage.quantity -= quantity_to_return

                # Update partner balance
                partner_id = request.form.get('partner_id')
                partner = Partner.query.get_or_404(partner_id)
                partner.balance += quantity_to_return

                db.session.commit()
                flash(f'{quantity_to_return} units returned to {partner.name}.', 'success')
            else:
                flash('Invalid return quantity!', 'error')

     # Retrieve all partners and small storages
     partners = Partner.query.all()
     small_storages = SmallStorage.query.all()
     return render_template('partners.html', form=form, partners=partners, small_storages=small_storages)


    @app.route('/create_small_storage', methods=['GET', 'POST'])
    def create_small_storage():
     form = SmallStorageForm()
     form.partner_id.choices = [(p.id, p.name) for p in Partner.query.all()]

     if form.validate_on_submit():
        name = form.name.data
        quantity = form.quantity.data
        partner_id = form.partner_id.data

        partner = Partner.query.get(partner_id)
        if partner:
            partner.balance -= quantity
            small_storage = SmallStorage(name=name, quantity=quantity, partner_id=partner_id)
            db.session.add(small_storage)
            db.session.commit()
            flash('Amount transferred to Small Storage!', 'success')
            return redirect(url_for('create_small_storage'))
        else:
            flash('Partner not found!', 'error')

     small_storages = SmallStorage.query.all()
     partners = Partner.query.all()
     cards = Card.query.all()  # Fetch cards to pass to the template
     return render_template('create_small_storage.html', form=form, small_storages=small_storages, partners=partners, cards=cards)

    
#////////////////////edit delete add//////////////////////////////////////////////
    @app.route('/delete_small_storage/<int:id>', methods=['POST'])
    def delete_small_storage(id):
     small_storage = SmallStorage.query.get_or_404(id)
     # Return quantity to partner's balance
     partner = Partner.query.get(small_storage.partner_id)
     partner.balance += small_storage.quantity
     db.session.delete(small_storage)
     db.session.commit()
     flash('Small storage deleted successfully!', 'success')
     return redirect(url_for('create_small_storage'))

   
    
    @app.route('/delete_partner/<int:id>', methods=['POST'])
    def delete_partner(id):
     partner = Partner.query.get_or_404(id)
     db.session.delete(partner)
     db.session.commit()
     flash('Partner deleted successfully!', 'success')
     return redirect(url_for('partners'))
    
    @app.route('/edit_small_storage', methods=['POST'])
    def edit_small_storage():
     small_storage_id = request.form.get('id')
     name = request.form.get('name')
     quantity = int(request.form.get('quantity'))  # Ensure quantity is an integer
     partner_id = request.form.get('partner_id')

     small_storage = SmallStorage.query.get_or_404(small_storage_id)
     small_storage.name = name
     small_storage.quantity += quantity  # Add the new quantity to the existing quantity
     small_storage.partner_id = partner_id

     try:
        # Update partner balance
        partner = Partner.query.get_or_404(partner_id)
        partner.balance -= quantity
        db.session.commit()
        return jsonify({'success': True})
     except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
     
    

    @app.route('/return_small_storage/<int:small_storage_id>', methods=['POST'])
    def return_small_storage(small_storage_id):
     # Retrieve data from form
     quantity = int(request.form['quantity'])
     partner_id = int(request.form['partner_id'])

     # Fetch Small Storage entry
     small_storage = SmallStorage.query.get_or_404(small_storage_id)

     # Fetch Partner entry
     partner = Partner.query.get_or_404(partner_id)

     try:
        # Update balances
        partner.balance += quantity  # Increase partner's balance
        small_storage.quantity -= quantity  # Decrease small storage quantity

        # Save changes
        db.session.commit()

        # Flash success message
        flash('Quantity returned successfully.', 'success')

        # Redirect back to small storage page after return
        return redirect(url_for('create_small_storage'))
     except Exception as e:
        flash(f'Error returning quantity: {str(e)}', 'error')
        return redirect(url_for('create_small_storage'))
     
#EXCEL IZVESTAJ///////////////////////////////////////
     
    
    
    
        