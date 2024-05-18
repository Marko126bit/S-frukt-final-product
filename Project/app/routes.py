# routes.py
from datetime import datetime
from flask import  jsonify, render_template, request, url_for, flash, redirect, send_file
from sqlalchemy import Transaction, func
from .forms import DeletePartnerForm, LoginForm,  PartnerForm, SmallStorageForm, TransactionForm
from .models import  Partner,  SmallStorage, User, Partner
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
    @app.route('/adjust_main_storage', methods=['GET'])
    def adjust_main_storage_page():
     # Render the HTML page with context data
     return render_template('adjust_main_storage.html')

    
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
     return render_template('create_small_storage.html', form=form, small_storages=small_storages)

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
#EXCEL IZVESTAJ///////////////////////////////////////
    
   
        