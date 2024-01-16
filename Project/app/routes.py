# routes.py
from flask import abort, jsonify, render_template, request, url_for, flash, redirect
from .forms import  AdjustMainStorageForm, LoginForm,  SmallStorageForm, PartnerForm
from .models import MainStorage, Partner, SmallStorage, User
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
    
   #logic for small and partner/////////////////////////////////////////////////
    @app.route('/adjust_main_storage', methods=['GET'])
    def adjust_main_storage_page():
     # Render the HTML page with context data
     return render_template('adjust_main_storage.html')


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
    @app.route('/get_main_storage_quantity', methods=['GET']) 
    def get_main_storage_quantity():
     main_storage = MainStorage.get_main_storage()
     if main_storage:
        return jsonify({'quantity': main_storage.total_quantity})
     else:
        return jsonify({'error': 'Main storage not found'}), 404

    @app.route('/get_entities_by_type', methods=['GET'])
    def get_entities_by_type():
     entity_type = request.args.get('type')
     if entity_type == 'partner':
        partners = Partner.query.all()
        partner_list = [{'id': partner.id, 'name': partner.name, 'quantity': partner.quantity} for partner in partners]
        return jsonify(partner_list)
     elif entity_type == 'storage':
        storages = SmallStorage.query.all()
        storage_list = [{'id': storage.id, 'name': storage.name, 'quantity': storage.quantity} for storage in storages]
        return jsonify(storage_list)
     else:
        return jsonify({'error': 'Invalid entity type'}), 400

    @app.route('/adjust_main_storage', methods=['POST'])
    def adjust_main_storage():
     data = request.get_json()
     partner_name = data.get('partner_name')
     quantity = data.get('quantity')
     operation = data.get('operation')  # 'add' or 'subtract'

     storage = MainStorage.get_main_storage()
     partner = Partner.query.filter_by(name=partner_name).first()

     if not partner or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid input'}), 400

     try:
        if operation == 'add':
            # Assuming storage has a method to add quantity
            new_quantity = storage.add_quantity(quantity, partner)
        elif operation == 'subtract':
            # Assuming storage has a method to subtract quantity
            new_quantity = storage.subtract_quantity(quantity, partner)
        else:
            return jsonify({'error': 'Invalid operation'}), 400
        
        db.session.commit()
        return jsonify({'message': 'Main storage adjusted', 'new_quantity': new_quantity})
     except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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













