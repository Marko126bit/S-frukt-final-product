# routes.py
from flask import abort, jsonify, render_template, request, url_for, flash, redirect
from .forms import  AdjustMainStorageForm, LoginForm,  SmallStorageForm, PartnerForm
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

    @app.route('/main_storage', methods=['GET', 'POST'])
    def adjust_main_storage():
     form = AdjustMainStorageForm()

    # Dynamically populate entity_id choices based on entity_type
     if request.method == 'POST':
        entity_type = form.entity_type.data
        if entity_type == 'partner':
            form.entity_id.choices = [(partner.id, partner.name) for partner in Partner.query.all()]
        elif entity_type == 'small_storage':
            form.entity_id.choices = [(storage.id, storage.name) for storage in SmallStorage.query.all()]

     if form.validate_on_submit():
        entity_id = form.entity_id.data
        quantity = form.quantity.data
        action = form.action.data

        main_storage = MainStorage.query.first()  # Assuming there's only one main storage record

        if entity_type == 'small_storage':
            entity = SmallStorage.query.get(entity_id)
        elif entity_type == 'partner':
            entity = Partner.query.get(entity_id)

        if not entity:
            flash(f'{entity_type.title()} not found.', 'error')
            return redirect(url_for('adjust_main_storage'))

        if action == 'add':
            if entity.quantity >= quantity:
                entity.quantity -= quantity
                main_storage.total_quantity += quantity
            else:
                flash(f'Insufficient quantity in {entity_type}.', 'error')
                return redirect(url_for('adjust_main_storage'))
        elif action == 'subtract':
            if main_storage.total_quantity >= quantity:
                main_storage.total_quantity -= quantity
                entity.quantity += quantity
            else:
                flash('Insufficient quantity in main storage.', 'error')
                return redirect(url_for('adjust_main_storage'))

        db.session.commit()
        flash('Main storage adjusted successfully.', 'success')
        return redirect(url_for('adjust_main_storage'))

     return render_template('adjust_main_storage.html', form=form)



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

    #transfer logic ////////////////////////////////////////////////////////////


    @app.route('/main_storage/subtract', methods=['POST'])
    def subtract_from_main_storage():
     entity_type = request.form['entity_type']
     entity_id = int(request.form['entity_id'])
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
     try:
        db.session.query(MainStorageTransaction).delete()
        db.session.commit()
        flash('All transactions deleted.', 'success')
     except Exception as e:
        db.session.rollback()
        flash('An error occurred. Not all transactions were deleted.', 'error')

     return redirect(url_for('main_storage'))

   
    @app.route('/get_entities')
    def get_entities():
     entity_type = request.args.get('type', type=str)
     entities = []
     if entity_type == 'partner':
        partners = Partner.query.all()
        entities = [(partner.id, partner.name) for partner in partners]
     elif entity_type == 'small_storage':
        storages = SmallStorage.query.all()
        entities = [(storage.id, storage.name) for storage in storages]
     # Add handling for other entity types if necessary
     return jsonify(entities)
#////////////////////edit delete add//////////////////////////////////////////////
    @app.route('/small_storage/edit/<int:storage_id>', methods=['POST'])
    def edit_small_storage(storage_id):
     storage = SmallStorage.query.get_or_404(storage_id)
     name = request.form.get('name')
     quantity = request.form.get('quantity', type=int)

     if name:
        storage.name = name
     if quantity is not None:  # Check for `None` because `0` is a valid quantity
        storage.quantity = quantity
     db.session.commit()

     return jsonify({'success': 'Storage updated', 'storage_id': storage.id, 'name': storage.name, 'quantity': storage.quantity})


    @app.route('/partner/edit/<int:partner_id>', methods=['POST'])
    def edit_partner(partner_id):
     partner = Partner.query.get_or_404(partner_id)
     name = request.form.get('name')
     quantity = request.form.get('quantity', type=int)

     if name:
         partner.name = name
     if quantity is not None:  # Check for `None` because `0` is a valid quantity
        partner.quantity = quantity
     db.session.commit()

     return jsonify({'success': 'Partner updated', 'partner_id': partner.id, 'name': partner.name, 'quantity': partner.quantity})

    @app.route('/small_storage/delete/<int:storage_id>', methods=['POST'])
    def delete_small_storage(storage_id):
     storage = SmallStorage.query.get_or_404(storage_id)
     db.session.delete(storage)
     db.session.commit()
     return jsonify({'success': 'Small storage deleted', 'storage_id': storage_id})
    
    @app.route('/partner/delete/<int:partner_id>', methods=['POST'])
    def delete_partner(partner_id):
     partner = Partner.query.get_or_404(partner_id)
     db.session.delete(partner)
     db.session.commit()
     return jsonify({'success': 'Partner deleted', 'partner_id': partner_id}
                    )
    
    @app.route('/partner/delete_all', methods=['POST']) 
    def delete_all_partners():
     Partner.query.delete()
     db.session.commit()
     return jsonify({'success': 'All partners deleted'})
    
    @app.route('/small_storage/delete_all', methods=['POST'])
    def delete_all_small_storages():
     SmallStorage.query.delete()
     db.session.commit()
     return jsonify({'success': 'All small storages deleted'})













