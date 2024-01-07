# routes.py
import datetime
from flask import abort, render_template, request, url_for, flash, redirect
from .forms import  LoginForm, PartnerForm, SmallStorageForm
from .models import MainStorage, MainStorageTransaction, Partner, SmallStorage, User
from .extensions import db
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash


def configure_routes(app):

    @app.route('/')
    def home():
        return render_template('home.html')
#log in system
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
                flash('Login Unsuccessful. Please check username and password', 'danger')
        
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('home'))
    
   #logic for main,small and partner

    @app.route('/partners', methods=['GET', 'POST'])
    def partners():
     form = PartnerForm()
     if form.validate_on_submit():
        partner = Partner(name=form.name.data, quantity=form.quantity.data)
        db.session.add(partner)
        db.session.commit()
        flash('New partner created!', 'success')
        return redirect(url_for('partners'))
    
     all_partners = Partner.query.all()  # Fetch all partners from the database
     return render_template('partners.html', form=form, partners=all_partners)

    @app.route('/create_small_storage', methods=['GET', 'POST'])
    def create_small_storage():
     form = SmallStorageForm()
     if form.validate_on_submit():
        new_storage = SmallStorage(name=form.name.data, quantity=form.quantity.data)
        db.session.add(new_storage)
        db.session.commit()
        flash('New small storage created!', 'success')
        return redirect(url_for('create_small_storage'))
    
     small_storages = SmallStorage.query.all()
     return render_template('create_small_storage.html', form=form, small_storages=small_storages)

    
    @app.route('/main_storage', methods=['GET', 'POST'])
    def main_storage():
     main_storage = MainStorage.query.first()
     if request.method == 'POST':
        try:
            # Adjust quantity based on form input (not shown here)
            quantity = int(request.form['quantity'])
            main_storage.adjust_quantity(quantity)
            flash('Main storage quantity adjusted.', 'success')
        except ValueError as e:
            flash(str(e), 'error')
    
     return render_template('main_storage.html', main_storage=main_storage)

    #transfer logic 

    @app.route('/transfer_from_small_storage_to_main/<int:storage_id>', methods=['POST'])
    def transfer_from_small_storage_to_main(storage_id):
     small_storage = SmallStorage.query.get_or_404(storage_id)
     main_storage = MainStorage.query.first_or_404()
     quantity = int(request.form.get('quantity'))

     if small_storage.quantity >= quantity:
        small_storage.quantity -= quantity
        main_storage.total_quantity += quantity
        transaction = MainStorageTransaction(
            quantity=quantity, 
            action='give', 
            entity_type='small_storage', 
            entity_id=small_storage.id
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transfer successful!', 'success')
     else:
        flash('Insufficient quantity in small storage.', 'danger')

     return redirect(url_for('main_storage.html',storage_id=create_small_storage.id))
    

    @app.route('/partner/<int:partner_id>/transaction', methods=['POST'])
    def partner_transaction(partner_id):
     partner = Partner.query.get_or_404(partner_id)
     main_storage = MainStorage.query.first()
     quantity = int(request.form.get('quantity'))
     action = request.form.get('action')  # 'give' or 'take'

     try:
         if action == 'give':
            quantity_given = partner.give_to_main(quantity)
            main_storage.adjust_quantity(quantity_given)
            transaction_type = 'give'
         elif action == 'take':
            partner.take_from_main(quantity, main_storage)
            transaction_type = 'take'
         else:
            raise ValueError('Invalid action')

        # Log the transaction
         transaction = MainStorageTransaction(
            quantity=quantity,
            action=transaction_type,
            entity_type='partner',
            entity_id=partner_id,
            timestamp=datetime.utcnow()
        )
         db.session.add(transaction)

         db.session.commit()
         flash(f'Transaction successful: {action} {quantity}', 'success')
     except ValueError as e:
        db.session.rollback()
        flash(str(e), 'danger')

     return redirect(url_for('main_storage.html', partner_id=partner_id))
    

   



   



