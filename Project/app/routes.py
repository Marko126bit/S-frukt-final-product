# routes.py
from flask import abort, render_template, request, url_for, flash, redirect
from .forms import  LoginForm, StorageForm
from .models import MainStorage, Partner, SmallStorage, User, Storage, get_main_storage_data
from .extensions import db, cache
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash


def configure_routes(app):

    @app.route('/')
    def home():
        return render_template('home.html')

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
    
    @login_required
    @app.route('/storage/new', methods=['GET', 'POST'])
    def new_storage():
     form = StorageForm()
     if form.validate_on_submit():
        storage = Storage(name=form.name.data, user_id=current_user.id)
        db.session.add(storage)
        db.session.commit()
        flash('New storage has been created!', 'success')
        return redirect(url_for('view_storages'))
     return render_template('create_small_storage.html', title='New Storage', form=form)
    

    @app.route('/main_storage')
    @login_required
    def main_storage():
     main_storage = MainStorage.query.first()  # Assuming single main storage
     return render_template('main_storage.html', main_storage=main_storage)


    @app.route('/create_small_storage', methods=['GET', 'POST'])
    @login_required
    def create_small_storage():
     if request.method == 'POST':
        name = request.form.get('name')
        quantity = int(request.form.get('quantity', 0))
        new_storage = SmallStorage(name=name, quantity=quantity)
        db.session.add(new_storage)
        db.session.commit()
        small_storages = SmallStorage.query.all()
        flash('New small storage created!', 'success')

     small_storages = SmallStorage.query.all()
     return render_template('create_small_storage.html', small_storages=small_storages)

    @app.route('/storage_log/<int:storage_id>')
    @login_required
    def storage_log(storage_id):
     storage = SmallStorage.query.get_or_404(storage_id)
     logs = storage.transactions  # Assuming a relationship to a Transaction model
     return render_template('storage_log.html', storage=storage, logs=logs)
    
    @app.route('/partners') 
    @login_required
    def partners():
     all_partners = Partner.query.all()
     return render_template('partners.html', partners=all_partners)

    @app.route('/add_partner', methods=['GET', 'POST'])
    @login_required
    def add_partner():
     if request.method == 'POST':
        name = request.form.get('name')
        quantity = int(request.form.get('quantity', 0))
        partner = Partner(name=name, quantity=quantity)
        db.session.add(partner)
        db.session.commit()
        flash('New partner added!', 'success')
        return redirect(url_for('partners'))

     return render_template('add_partner.html')

    @app.route('/transfer', methods=['POST'])
    def transfer():
     entity_type = request.form.get('entity_type')
     entity_id = request.form.get('entity_id', type=int)
     quantity = request.form.get('quantity', type=int)
     action = request.form.get('action')

     main_storage = MainStorage.query.first_or_404()
     entity = None

     if entity_type == 'partner':
        entity = Partner.query.get_or_404(entity_id)
     elif entity_type == 'small_storage':
        entity = SmallStorage.query.get_or_404(entity_id)
     else:
        flash('Invalid entity type', 'danger')
        return redirect(url_for('home'))

     try:
         if action == 'give':
            entity.give_to_main(main_storage, quantity)
         elif action == 'take':
            entity.take_from_main(main_storage, quantity)
         else:
            flash('Invalid action', 'danger')
            return redirect(url_for('home'))

         db.session.commit()
         flash('Transfer successful!', 'success')

     except ValueError as e:
        flash(str(e), 'danger')
        db.session.rollback()

     return redirect(url_for('home'))
        
    @app.route('/small_storage/<int:storage_id>/transfer')
    @login_required
    def small_storage_transfer(storage_id):
     storage = SmallStorage.query.get_or_404(storage_id)
     return render_template('transfer.html', entity_id=storage.id, entity_type='small_storage')

    @app.route('/partner/<int:partner_id>/transfer')
    @login_required
    def partner_transfer(partner_id):
     partner = Partner.query.get_or_404(partner_id)
     return render_template('transfer.html', entity_id=partner.id, entity_type='partner')


    
    @app.route('/storages')
    @login_required
    def view_storages():
     storages = Storage.query.filter_by(user_id=current_user.id).all()
     return render_template('view_storage.html', storages=storages)

    @app.errorhandler(403)
    def forbidden(e):
     return render_template('403.html'), 403  # Ensure you have a 403.html template

    @app.route('/edit_storage/<int:storage_id>', methods=['GET', 'POST'])
    def edit_storage(storage_id):
     storage = Storage.query.get_or_404(storage_id)
     if request.method == 'POST':
        # Assuming there's a form to process the edit
        form = StorageForm(request.form)
        if form.validate_on_submit():
            # Process the validated form data and update storage
            storage.name = form.name.data
            # ... other fields
            db.session.commit()
            flash('Storage updated successfully!', 'success')
            return redirect(url_for('view_storages', storage_id=storage.id))
        else:
            # Form didn't validate, fall through to the render_template call
            flash('Error updating storage.', 'error')
            # GET request or failed POST validation: render the edit page
     form = StorageForm(obj=storage)
     return render_template('edit_storage.html', form=form, storage_id=storage_id)

    @app.route('/delete_storage/<int:storage_id>')
    @login_required
    def delete_storage(storage_id):
     storage = Storage.query.get_or_404(storage_id)
     if storage.user_id != current_user.id:
        abort(403)  # HTTP Forbidden status code
     db.session.delete(storage)
     db.session.commit()
     flash('Storage deleted successfully', 'success')
     return redirect(url_for('view_storages'))
