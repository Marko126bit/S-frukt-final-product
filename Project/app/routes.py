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
     if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])

        # Retrieve the single instance of main storage
        main_storage = MainStorage.query.get(1)  # Assuming you have only one instance of MainStorage

        if main_storage and main_storage.quantity >= quantity:
            # Subtract the quantity from the main storage
            main_storage.quantity -= quantity

            # Create and add the new small storage
            new_small_storage = SmallStorage(name=name, quantity=quantity, main_storage_id=main_storage.id)
            db.session.add(new_small_storage)
            db.session.commit()

            flash('New small storage created!', 'success')
            return redirect(url_for('create_small_storage'))
        else:
            # Not enough quantity in main storage to create small storage
            flash('Not enough quantity in main storage!', 'error')

    # For a GET request or if not enough quantity, just render the create page
     small_storages = SmallStorage.query.all()
     return render_template('create_small_storage.html', small_storages=small_storages)

    
    #transfer logic ////////////////////////////////////////////////////////////
    @app.route('/get_main_storage_quantity', methods=['GET']) 
    def get_main_storage_quantity():
     main_storage = MainStorage.get_main_storage()
     if main_storage:
        return jsonify({'quantity': main_storage.quantity})
     else:
        return jsonify({'error': 'Main storage not found'}), 404

    @app.route('/get_entities_by_type')
    def get_entities_by_type():
     entity_type = request.args.get('type')
     if entity_type == 'partner':
        # Replace with actual database query to get partners
        partners = [{'name': 'Partner One'}, {'name': 'Partner Two'}]
        return jsonify(partners)
     elif entity_type == 'storage':
        # Replace with actual database query to get storages
        storages = [{'name': 'Storage One'}, {'name': 'Storage Two'}]
        return jsonify(storages)
     else:
        return jsonify({'error': 'Invalid entity type'}), 400

    @app.route('/adjust_main_storage', methods=['POST'])
    def adjust_main_storage():
     data = request.get_json()
     partner_id = data.get('partner_id')  # Ensure you're getting the partner's ID
     quantity = data.get('quantity')
     operation = data.get('operation')

    # Retrieve the single MainStorage instance and the Partner instance by ID
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage instance
     partner = Partner.query.get(partner_id)

     if not main_storage or not partner:
        return jsonify({'error': 'Main storage or partner not found'}), 404

     if operation == 'add':
        # When adding to main storage, subtract the same quantity from the partner's storage
        if partner.quantity >= quantity:
            partner.quantity -= quantity
            main_storage.quantity += quantity
        else:
            return jsonify({'error': 'Partner does not have enough quantity to add to main storage'}), 400

     elif operation == 'subtract':
        # When subtracting from main storage, add the same quantity to the partner's storage
        if main_storage.quantity >= quantity:
            main_storage.quantity -= quantity
            partner.quantity += quantity
        else:
            return jsonify({'error': 'Not enough quantity in main storage to subtract'}), 400

     else:
        return jsonify({'error': 'Invalid operation'}), 400

    # Commit the changes to the database
     db.session.commit()
     return jsonify({
        'message': 'Storage adjusted successfully',
        'new_main_storage_quantity': main_storage.quantity,
        'new_partner_quantity': partner.quantity
     })


    @app.route('/get_quantities')
    def get_quantities():
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage instance
     partners = Partner.query.all()

     if not main_storage:
        return jsonify({'error': 'Main storage not found'}), 404

     partners_data = [{'id': partner.id, 'name': partner.name, 'quantity': partner.quantity} for partner in partners]

     return jsonify({
        'main_storage_quantity': main_storage.quantity,
        'partners': partners_data
     })

    @app.route('/get_small_storages', methods=['GET'])
    def get_small_storages():
     # Query all small storages and return their details
     small_storages = SmallStorage.query.all()
     storages_data = [{'id': storage.id, 'name': storage.name, 'quantity': storage.quantity} for storage in small_storages]
     return jsonify({'storages': storages_data})

    @app.route('/get_partners')
    def get_partners():
     partners = Partner.query.with_entities(Partner.id, Partner.name).all()
     partner_list = [{'id': partner.id, 'name': partner.name} for partner in partners]
     return jsonify(partner_list)
    

    @app.route('/adjust_small_storage', methods=['POST'])
    def adjust_small_storage():
     data = request.get_json()
     small_storage_id = data.get('small_storage_id')
     quantity = data.get('quantity')
     operation = data.get('operation')

    # Retrieve the small storage instance
     small_storage = SmallStorage.query.get(small_storage_id)
     # Retrieve the single MainStorage instance
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage instance

     if not small_storage or not main_storage:
         return jsonify({'error': 'Small storage or main storage not found'}), 404

     if operation == 'add':
        # Ensure main_storage has enough quantity to deduct
        if main_storage.quantity >= quantity:
            main_storage.quantity -= quantity
            small_storage.quantity += quantity
        else:
            return jsonify({'error': 'Not enough quantity in main storage'}), 400
     elif operation == 'subtract':
        # Ensure small_storage has enough quantity to give back
        if small_storage.quantity >= quantity:
            small_storage.quantity -= quantity
            main_storage.quantity += quantity
        else:
            return jsonify({'error': 'Not enough quantity in small storage'}), 400
     else:
        return jsonify({'error': 'Invalid operation'}), 400

    # Commit the changes to the database
     db.session.commit()

     return jsonify({
        'message': 'Storage adjusted successfully',
        'new_main_storage_quantity': main_storage.quantity,
        'new_small_storage_quantity': small_storage.quantity
    })



#////////////////////edit delete add//////////////////////////////////////////////


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
    
    @app.route('/return_all_to_partners', methods=['POST'])
    def return_all_to_partners():
     with db.session.begin():
        # Retrieve the main storage instance and all partner instances
        main_storage = MainStorage.query.first()
        partners = Partner.query.all()

        if not main_storage:
            return jsonify({'error': 'Main storage not found'}), 404

        if not partners:
            return jsonify({'error': 'No partners found'}), 404

        # Calculate the total quantity to be distributed to each partner
        total_quantity = main_storage.quantity
        if total_quantity <= 0:
            return jsonify({'error': 'No quantity in main storage to distribute'}), 400

        quantity_per_partner = total_quantity // len(partners)

        # Distribute the quantities
        for partner in partners:
            partner.quantity += quantity_per_partner
            main_storage.quantity -= quantity_per_partner

        # Handle any remaining quantity due to integer division
        remainder = total_quantity % len(partners)
        if remainder > 0:
            # Here you can decide how to distribute the remainder
            # For example, adding it to the first partner
            partners[0].quantity += remainder
            main_storage.quantity -= remainder

        try:
            db.session.commit()
            message = 'Quantities returned to all partners successfully'
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

     return jsonify({
        'message': message,
        'new_main_storage_quantity': main_storage.quantity,
        'distributed_quantities': {partner.id: partner.quantity for partner in partners}
     })



    @app.route('/edit_small_storage', methods=['POST'])
    def edit_small_storage():
     data = request.get_json()
     small_storage_id = data['id']
     new_name = data.get('name', '').strip()  # Default to empty string if name is not provided
     new_quantity = data.get('quantity', None)  # Default to None if quantity is not provided

     small_storage = SmallStorage.query.get(small_storage_id)
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage

     if small_storage and main_storage:
        # Initialize a flag to check if we need to update the main storage quantity
        update_main_storage = False

        # Update the name only if a new name was provided and it is different
        if new_name and new_name != small_storage.name:
            small_storage.name = new_name

        # Update the quantity only if a new quantity was provided and it is different
        if new_quantity is not None:
            new_quantity = int(new_quantity)
            if new_quantity != small_storage.quantity:
                # Calculate the quantity difference
                quantity_difference = new_quantity - small_storage.quantity

                # Check if there is enough in the main storage to accommodate the change
                if main_storage.quantity >= quantity_difference:
                    main_storage.quantity -= quantity_difference
                    small_storage.quantity = new_quantity
                    update_main_storage = True
                else:
                    return jsonify({'error': 'Not enough quantity in main storage'}), 400

        # Commit changes to the database only if there are changes to commit
        if new_name or update_main_storage:
            db.session.commit()
            return jsonify({'success': 'Storage updated successfully'})
        else:
            # If there are no changes, no need to commit and we return a message
            return jsonify({'success': 'No changes made to storage'})

     else:
        return jsonify({'error': 'Storage not found'}), 404


    @app.route('/delete_small_storage', methods=['POST'])
    def delete_small_storage():
     data = request.get_json()
     small_storage_id = data['id']
    
     small_storage = SmallStorage.query.get(small_storage_id)
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage
    
     if small_storage and main_storage:
        main_storage.quantity += small_storage.quantity
        db.session.delete(small_storage)
        db.session.commit()
        return jsonify({'success': 'Storage deleted successfully'})
     else:
        return jsonify({'error': 'Storage not found'}), 404

    @app.route('/delete_all_small_storages', methods=['POST'])
    def delete_all_small_storages():
     main_storage = MainStorage.query.get(1)  # Assuming there's only one main storage
    
     if main_storage:
        small_storages = SmallStorage.query.all()
        for storage in small_storages:
            main_storage.quantity += storage.quantity
        num_rows_deleted = db.session.query(SmallStorage).delete()
        db.session.commit()
        return jsonify({'success': f'{num_rows_deleted} storages deleted successfully'})
     else:
        return jsonify({'error': 'Main storage not found'}), 404

    











