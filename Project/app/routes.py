# routes.py
import datetime
from flask import abort, render_template, request, url_for, flash, redirect
from .forms import  LoginForm, PartnerForm, SmallStorageForm, StorageForm
from .models import MainStorage, MainStorageTransaction, Partner, SmallStorage, User
from .extensions import db
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash


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
                flash('Login Unsuccessful. Please check username and password', 'danger')
        
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('home'))
    
   #logic for main,small and partner/////////////////////////////////////////////////

    @app.route('/partners', methods=['GET', 'POST'])
    def partners():
     form = PartnerForm()
     if form.validate_on_submit():
        partner = Partner(name=form.name.data, quantity=form.quantity.data)
        db.session.add(partner)
        db.session.commit()
        flash('New partner created!', 'success')
        return redirect(url_for('partners'))
    
     all_partners = Partner.query.all()
     partner_names = {partner.id: partner.name for partner in all_partners}

     return render_template('partners.html', form=form, partners=all_partners, partner_names=partner_names)

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
     small_storage_names = {storage.id: storage.name for storage in small_storages}

     return render_template('create_small_storage.html', form=form, small_storages=small_storages, small_storage_names=small_storage_names)

    
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

    #transfer logic ////////////////////////////////////////////////////////////

    @app.route('/main_storage/subtract', methods=['POST'])
    def subtract_from_main_storage():
     entity_type = request.form['entity_type']
     entity_id = request.form['entity_id']
     quantity = int(request.form['quantity'])

     # Get the main storage
     main_storage = MainStorage.query.first()

     if main_storage.total_quantity >= quantity:
        # Perform the subtraction
        main_storage.total_quantity -= quantity

        # Create a transaction record
        transaction = MainStorageTransaction(
            quantity=quantity,
            action='subtract',
            entity_type=entity_type,
            entity_id=entity_id
        )
        db.session.add(transaction)

        # Commit the session
        try:
            db.session.commit()
            flash('Quantity subtracted from main storage.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Transaction failed.', 'error')
     else:
        flash('Not enough quantity in main storage.', 'error')

     return redirect(url_for('main_storage'))
    

    @app.route('/add_to_main_storage', methods=['POST'])
    def add_to_main_storage():
     form = StorageForm()  # Assuming you have a form class named StorageForm
    
     if form.validate_on_submit():
        entity_type = form.entity_type.data  # 'partner' or 'small_storage'
        entity_id = form.entity_id.data
        quantity = form.quantity.data

        # Check if the storage entity exists
        if entity_type == 'partner':
            entity = Partner.query.get(entity_id)
        elif entity_type == 'small_storage':
            entity = SmallStorage.query.get(entity_id)
        
        if not entity or quantity <= 0:
            flash('Invalid storage entity or quantity.', 'error')
            return redirect(url_for('main_storage'))

        # Check if the main storage has enough quantity to subtract
        main_storage = MainStorage.query.first()
        if quantity > main_storage.total_quantity and form.action.data == 'subtract':
            flash('Not enough quantity in main storage.', 'error')
            return redirect(url_for('main_storage'))

        # Adjust the main storage quantity
        if form.action.data == 'add':
            main_storage.total_quantity += quantity
        elif form.action.data == 'subtract':
            main_storage.total_quantity -= quantity

        # Record the transaction
        transaction = MainStorageTransaction(
            entity_id=entity_id,
            entity_type=entity_type,
            action=form.action.data,
            quantity=quantity,
            timestamp=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Main storage adjusted.', 'success')
     else:
        flash('Error in form submission.', 'error')

     return redirect(url_for('main_storage'))

    @app.route('/main_storage/transaction/<int:transaction_id>/delete', methods=['POST'])
    def delete_transaction(transaction_id):
     transaction = MainStorageTransaction.query.get_or_404(transaction_id)
     db.session.delete(transaction)
     try:
        db.session.commit()
        flash('Transaction deleted.', 'success')
     except Exception as e:
        db.session.rollback()
        flash('An error occurred. Transaction not deleted.', 'error')

     return redirect(url_for('main_storage'))
    

    @app.route('/main_storage/transactions/delete_all', methods=['POST'])
    def delete_all_transactions():
     db.session.query(MainStorageTransaction).delete()
     db.session.commit()


   



   



